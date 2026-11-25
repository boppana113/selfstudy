"""Local server for /dsa live voice mock interviews.

The browser page (call.html) does the audio: Chrome's speech recognition for
your voice, speechSynthesis for the interviewer's. This server holds the API
key and runs the interviewer, so the key never reaches the browser.

API key protection:
  - read from the macOS Keychain at startup (store it with set-key.sh); never
    written to disk, env vars, logs, or the transcript
  - the server binds to 127.0.0.1 only
  - every API call needs a random per-run token (in the URL fragment, sent as
    a header), and the Host header must be localhost, so other web pages open
    in your browser can't drive it or spend your key

The /dsa skill writes the problem brief (dsa/call/.brief.json) first.
Transcript: dsa/calls/<date>-<slug>.md, which /dsa debriefs from.

Usage: dsa/call/run.sh [--model claude-opus-5-5] [--effort low] [--port 8765]
"""

import argparse
import collections
import hashlib
import json
import secrets
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import anthropic

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]  # selfstudy/
BRIEF = HERE / ".brief.json"
PAGE = HERE / "call.html"
CALLS = ROOT / "dsa" / "calls"
KEYCHAIN_SERVICE = "dsa-call-anthropic"
# List prices per 1M tokens for the end-of-call estimate.
PRICES = {
    "claude-opus-5-5": {"in": 4.00, "out": 20.00, "cache_read": 0.20, "cache_write": 5.00},
    "claude-sonnet-5-5": {"in": 2.00, "out": 10.00, "cache_read": 0.10, "cache_write": 2.50},
    "claude-haiku-5-5": {"in": 0.10, "out": 0.50, "cache_read": 0.01, "cache_write": 0.125},
}

SYSTEM = """You are a software engineer at a large tech company running a live, spoken coding interview over a call. The candidate is preparing for MAANG loops. Your words are turned into speech, so write only what you would say out loud.

How you speak:
- 1 to 3 short sentences per turn. Plain spoken English. No markdown, no code, no symbols, no lists.
- Say complexities in words: "big O of n log n", "n squared".
- Latency-sensitive; begin your visible answer immediately.

Messages you receive:
- Lines starting with "CANDIDATE:" are a speech-to-text transcript of the candidate. Expect transcription errors; read generously.
- Lines starting with "EVENT:" come from the call software, not the candidate (code saved, long silence, time warnings). Code arrives in [CODE] blocks.
- Every message starts with [t=MM:SS], the time since the interview started.

When to stay silent:
- Reply with exactly SILENT (nothing else) when a real interviewer would say nothing: the candidate is thinking aloud mid-thought and hasn't asked you anything, or a code event shows nothing worth interrupting.
- Most code events should get SILENT. Speak on a code event only when: the code clearly isn't heading toward the approach they stated, or can't meet the complexity they claimed; a bug that will sink the approach (not a typo or an unfinished line) has survived two saves (ask about it, never name the fix: "What happens on that line when the window is empty?"); or the planned "why" interruption fits.
- At most one unprompted comment every 3 minutes.

How you run the interview (the brief below has the problem):
1. Open with the spoken prompt from the brief, then stop talking. Do not give constraints, sizes, edge cases, or the output format unless asked. Answer clarifying questions concretely and consistently with the brief.
2. They must state an approach and its time and space complexity before coding. If they start coding first, say once: "Before you code, what's the approach and the complexity?" If they propose brute force, accept it and ask "Can we do better?"
3. Once, partway through coding, ask one short "why" about a choice they made.
4. Hints only when they ask or are clearly stuck after a long silence. Give exactly one level of the brief's hint ladder per request, in order, never skipping ahead.
5. When they say they're done, ask them to trace their code by hand on the trace example from the brief. If the trace exposes a bug, let them fix it.
6. If time allows after a working solution, give the brief's follow-up twist and discuss the approach only.
7. When the trace (and twist, if any) is finished, or time is up, say a short neutral closing line like "Okay, let's stop there, thanks." and end that message with [END].
- Never teach, never give the solution, never grade during the call. Stay in character. Do not reveal the hint ladder, the optimal approach, or that you have a brief.

The brief:
{brief}
"""


def read_key():
    r = subprocess.run(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True, text=True,
    )
    key = r.stdout.strip()
    if r.returncode or not key:
        sys.exit("No API key in the Keychain. Run dsa/call/set-key.sh first (once).")
    return key


class Interview:
    def __init__(self, args, key):
        self.args = args
        self.brief = json.loads(BRIEF.read_text())
        self.file = ROOT / self.brief["practice_file"]
        self.client = anthropic.Anthropic(api_key=key)
        self.system = SYSTEM.format(brief=json.dumps(self.brief, indent=2))
        self.history = []
        self.lock = threading.Lock()  # one interviewer turn at a time
        self.t0 = None
        self.last_code_sent = None
        self.usage = collections.Counter()
        self.ended = False
        CALLS.mkdir(exist_ok=True)
        self.transcript = CALLS / f"{datetime.now():%Y-%m-%d-%H%M}-{self.brief['slug']}.md"

    # ---------- transcript ----------
    def ts(self):
        s = int(time.time() - (self.t0 or time.time()))
        return f"{s // 60:02d}:{s % 60:02d}"

    def log(self, text):
        with open(self.transcript, "a") as f:
            f.write(text)

    def start(self):
        if self.t0 is None:
            self.t0 = time.time()
            self.log(
                f"# Call: {self.brief.get('title', self.brief['slug'])}\n\n"
                f"Started {datetime.now():%Y-%m-%d %H:%M} · model {self.args.model} (effort {self.args.effort}) · "
                f"format {self.brief.get('format', 'generic')} · budget {self.brief.get('budget_min', 25)} min · "
                f"file `{self.brief['practice_file']}`\n\n"
            )
        return {
            "title": self.brief.get("title", self.brief["slug"]),
            "budget_min": self.brief.get("budget_min", 25),
            "file": self.brief["practice_file"],
        }

    # ---------- code ----------
    def code_now(self):
        return self.file.read_text() if self.file.exists() else ""

    def code_hash(self):
        return hashlib.md5(self.code_now().encode()).hexdigest()

    def build_turn(self, kind, text):
        parts = []
        if kind == "speech":
            parts.append(f"CANDIDATE: {text}")
        elif kind == "start":
            parts.append("EVENT: The candidate has joined the call. Start the interview.")
        elif kind == "code":
            parts.append(f"EVENT: code saved ({len(self.code_now().splitlines())} lines).")
        elif kind == "event":
            parts.append(f"EVENT: {text}")
        code = self.code_now()
        if code != self.last_code_sent and (kind == "code" or kind == "speech"):
            parts.append(f"[CODE {self.brief['practice_file']}]\n```python\n{code}\n```")
            self.last_code_sent = code
        return f"[t={self.ts()}] " + "\n".join(parts)

    # ---------- the interviewer ----------
    def turn(self, kind, text, send):
        """Run one interviewer turn, streaming NDJSON events through send(dict).
        send raises BrokenPipeError when the browser aborted (you talked over it)."""
        with self.lock:
            if kind == "speech":
                self.log(f"**[{self.ts()}] You:** {text}\n\n")
            content = self.build_turn(kind, text)
            msgs = self.history + [{"role": "user", "content": [
                {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}]}]
            out, sent, final, aborted = "", 0, None, False
            try:
                with self.client.beta.messages.stream(
                    model=self.args.model,
                    max_tokens=4000,
                    betas=["server-side-fallback-2026-07-01"],
                    fallbacks="default",
                    output_config={"effort": self.args.effort},
                    system=[{"type": "text", "text": self.system, "cache_control": {"type": "ephemeral"}}],
                    messages=msgs,
                ) as stream:
                    for chunk in stream.text_stream:
                        out += chunk
                        visible = out.replace("[END]", "")
                        if "SILENT".startswith(visible.strip()) or visible.strip().startswith("SILENT"):
                            continue  # hold back until we know it isn't SILENT
                        for k in range(4, 0, -1):  # hold back a half-arrived "[END]"
                            if visible.endswith("[END]"[:k]):
                                visible = visible[:-k]
                                break
                        if len(visible) > sent:
                            send({"t": "text", "v": visible[sent:]})
                            sent = len(visible)
                    final = stream.get_final_message()
            except (BrokenPipeError, ConnectionResetError):
                aborted = True
            except anthropic.APIError as e:
                self.log(f"_[{self.ts()}] API error: {type(e).__name__}_\n\n")
                try:
                    send({"t": "error", "v": f"API error: {type(e).__name__}"})
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return

            spoken = out.replace("[END]", "").strip()
            if aborted:
                if sent:  # interrupted mid-reply: keep what was said
                    self.history += [
                        {"role": "user", "content": content},
                        {"role": "assistant", "content": spoken[:sent] + " (interrupted by the candidate)"},
                    ]
                    self.log(f"**[{self.ts()}] Interviewer:** {spoken[:sent]} …(interrupted)\n\n")
                # nothing said yet: drop the turn; the page resends that speech with the next one
                return
            u = final.usage
            self.usage["in"] += u.input_tokens or 0
            self.usage["out"] += u.output_tokens or 0
            self.usage["cache_read"] += getattr(u, "cache_read_input_tokens", 0) or 0
            self.usage["cache_write"] += getattr(u, "cache_creation_input_tokens", 0) or 0
            self.history += [msgs[-1], {"role": "assistant", "content": final.content}]
            if final.stop_reason == "refusal":
                spoken = "Let's move on."
                send({"t": "text", "v": spoken})
            silent = spoken.startswith("SILENT")
            if silent:
                if kind == "code":
                    self.log(f"_[{self.ts()}] code saved ({len(self.code_now().splitlines())} lines), interviewer silent_\n\n")
                send({"t": "silent"})
            else:
                self.log(f"**[{self.ts()}] Interviewer:** {spoken}\n\n")
            ended = "[END]" in out
            send({"t": "done", "end": ended})

    def finish(self, why):
        if self.ended:
            return str(self.transcript.relative_to(ROOT))
        self.ended = True
        p = PRICES.get(self.args.model, PRICES["claude-opus-5-5"])
        cost = sum(self.usage[k] * p[k] for k in p) / 1e6
        mins = (time.time() - (self.t0 or time.time())) / 60
        self.log(
            f"---\n\nEnded {datetime.now():%H:%M} ({why}) · {mins:.1f} min · tokens in {self.usage['in']} / "
            f"out {self.usage['out']} / cache read {self.usage['cache_read']} / cache write {self.usage['cache_write']} · "
            f"est. cost ${cost:.2f} (list prices)\n\n## Final code\n\n```python\n{self.code_now()}\n```\n"
        )
        print(f"\n📞 call ended ({why}) · {mins:.1f} min · est. ${cost:.2f}")
        print(f"transcript: {self.transcript.relative_to(ROOT)}")
        print("Back in Claude Code, say: done with the call")
        return str(self.transcript.relative_to(ROOT))


def make_handler(iv, token, port):
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # keep the terminal quiet
            pass

        def guard(self, need_token=True):
            if self.headers.get("Host") not in allowed_hosts:
                self.send_error(403)
                return False
            if need_token and not secrets.compare_digest(self.headers.get("X-Call-Token", ""), token):
                self.send_error(403)
                return False
            return True

        def json_reply(self, obj):
            body = json.dumps(obj).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/" and self.guard(need_token=False):
                body = PAGE.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/api/code" and self.guard():
                self.json_reply({"hash": iv.code_hash(), "lines": len(iv.code_now().splitlines())})
            elif self.path not in ("/", "/api/code"):
                self.send_error(404)

        def do_POST(self):
            if not self.guard():
                return
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n) or b"{}")
            if self.path == "/api/start":
                self.json_reply(iv.start())
            elif self.path == "/api/turn":
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()

                def send(obj):
                    self.wfile.write((json.dumps(obj) + "\n").encode())
                    self.wfile.flush()

                iv.turn(data.get("kind", "speech"), data.get("text", ""), send)
            elif self.path == "/api/end":
                self.json_reply({"transcript": iv.finish(data.get("why", "ended from the page"))})
            else:
                self.send_error(404)

    return Handler


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="claude-opus-5-5", help="claude-opus-5-5 (default), claude-sonnet-5-5, or claude-haiku-5-5")
    p.add_argument("--effort", default="low", choices=["low", "medium", "high"], help="lower = faster replies")
    p.add_argument("--port", type=int, default=8765)
    args = p.parse_args()
    if not BRIEF.exists():
        sys.exit("No brief at dsa/call/.brief.json. Start with `/dsa call` in Claude Code, which writes it.")
    iv = Interview(args, read_key())
    token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(iv, token, args.port))
    url = f"http://localhost:{args.port}/#t={token}"
    print(f"Interview: {iv.brief.get('title', iv.brief['slug'])} · model {args.model}")
    print(f"Opening Chrome: {url}\n(Ctrl+C here ends the call and saves the transcript)")
    try:
        webbrowser.get("open -a 'Google Chrome' %s").open(url)
    except webbrowser.Error:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        iv.finish("Ctrl+C")


if __name__ == "__main__":
    main()
