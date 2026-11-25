"""Pull LeetCode progress for the DSA track.

Uses LeetCode's public GraphQL endpoint (the one the site itself calls). No
login or cookie: it only reads what a public profile shows. It's unofficial,
so if a query starts failing, check the field names first.

The API only returns the last ~20 accepted submissions, so history is kept in
lc-history.json and grows with every sync. Run it at the start of each session.

Writes:
  lc-history.json   every accepted problem seen so far (slug -> first/last solve, difficulty, tags)
  lc-snapshot.md    totals, solves per topic, and what's new since the last sync

Usage: python3 dsa/lc_sync.py [--quiet]
"""

import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

USER = "boppana113"
HERE = Path(__file__).parent
HISTORY = HERE / "lc-history.json"
SNAPSHOT = HERE / "lc-snapshot.md"
URL = "https://leetcode.com/graphql"


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com",
            "User-Agent": "Mozilla/5.0 (selfstudy sync)",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    if data.get("errors"):
        sys.exit(f"LeetCode API error: {data['errors']}")
    return data["data"]


PROFILE = """
query($u: String!) {
  matchedUser(username: $u) {
    submitStatsGlobal { acSubmissionNum { difficulty count } }
    tagProblemCounts {
      fundamental { tagName problemsSolved }
      intermediate { tagName problemsSolved }
      advanced { tagName problemsSolved }
    }
  }
  recentAcSubmissionList(username: $u, limit: 20) { title titleSlug timestamp }
}
"""

QUESTION = """
query($s: String!) { question(titleSlug: $s) { difficulty topicTags { name } } }
"""


def day(ts):
    return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")


def main():
    quiet = "--quiet" in sys.argv
    hist = json.loads(HISTORY.read_text()) if HISTORY.exists() else {"problems": {}, "last_sync": None}
    probs = hist["problems"]

    d = gql(PROFILE, {"u": USER})
    user = d["matchedUser"]
    if user is None:
        sys.exit(f"No public LeetCode profile for {USER}")

    new = []
    for s in reversed(d["recentAcSubmissionList"]):  # oldest first
        slug, ts = s["titleSlug"], int(s["timestamp"])
        p = probs.get(slug)
        if p is None:
            q = gql(QUESTION, {"s": slug})["question"] or {}
            p = probs[slug] = {
                "title": s["title"],
                "difficulty": q.get("difficulty", "?"),
                "tags": [t["name"] for t in q.get("topicTags", [])],
                "first": ts,
                "last": ts,
                "accepted_days": [],
            }
        if ts > p["last"]:
            p["last"] = ts
        p["first"] = min(p["first"], ts)
        if day(ts) not in p["accepted_days"]:
            p["accepted_days"].append(day(ts))
            p["accepted_days"].sort()
            if hist["last_sync"] is None or ts > hist["last_sync"]:
                new.append((day(ts), p["title"], p["difficulty"]))

    hist["last_sync"] = max([hist["last_sync"] or 0] + [int(s["timestamp"]) for s in d["recentAcSubmissionList"]])
    hist["totals"] = {x["difficulty"]: x["count"] for x in user["submitStatsGlobal"]["acSubmissionNum"]}
    HISTORY.write_text(json.dumps(hist, indent=2) + "\n")

    t = hist["totals"]
    tags = []
    for level in ("fundamental", "intermediate", "advanced"):
        tags += [(x["tagName"], x["problemsSolved"]) for x in user["tagProblemCounts"][level]]
    tags.sort(key=lambda x: -x[1])

    lines = [
        "# LeetCode snapshot",
        "",
        f"Written by `lc_sync.py` on {datetime.now():%Y-%m-%d %H:%M}. Don't edit; it's overwritten.",
        "",
        f"**Solved:** {t.get('All', 0)} total · {t.get('Easy', 0)} easy · {t.get('Medium', 0)} medium · {t.get('Hard', 0)} hard",
        "",
        "## New since last sync",
        "",
    ]
    lines += [f"- {dt} · {title} ({diff})" for dt, title, diff in new] or ["- none"]
    lines += ["", "## Solved per topic (LeetCode tags)", "", "| Topic | Solved |", "|---|---|"]
    lines += [f"| {name} | {n} |" for name, n in tags if n]
    lines += ["", "## Seen in history (most recent first)", "", "| Last solved | Problem | Difficulty | Times |", "|---|---|---|---|"]
    for p in sorted(probs.values(), key=lambda p: -p["last"]):
        lines.append(f"| {day(p['last'])} | {p['title']} | {p['difficulty']} | {len(p['accepted_days'])} |")
    SNAPSHOT.write_text("\n".join(lines) + "\n")

    if not quiet:
        print(f"{USER}: {t.get('All', 0)} solved ({t.get('Easy', 0)}E / {t.get('Medium', 0)}M / {t.get('Hard', 0)}H)")
        print(f"new since last sync: {len(new)}")
        for dt, title, diff in new:
            print(f"  {dt}  {title} ({diff})")


if __name__ == "__main__":
    main()
