"""Sync cards/*.md into the Space app (getspace.app) via the local `space` CLI.

Card file format (one file per topic slug):

    # Kafka                      <- topic: one Space deck, "SD · Kafka"
    ## Consumer groups           <- subtopic: organizes the file only (space-cli
                                    0.2.0 fails to assign cards to groups)
    Q: question (can span lines, ``` blocks allowed)
    A: the pick and its cost, 1-2 sentences
    Why: a concrete walkthrough (one request, one user, real numbers)
    Flip: optional, when you'd choose differently
    Staff: optional stretch line, shown under the answer

Space has no card IDs we control, so a card is matched by its question text
within its deck. Re-running is safe: new questions are created, changed
answers are edited in place (learning history kept), unchanged cards are
skipped. Changing a question creates a new card; the old one is listed as
orphaned and soft-deleted only with --prune.

Deck IDs live in space-ids.json next to this script.

Usage: python3 space_sync.py [slug ...] [--dry-run] [--prune]
"""

import json
import re
import subprocess
import sys
from pathlib import Path

DECK_PREFIX = "SD · "
HERE = Path(__file__).parent
IDS = HERE / "space-ids.json"


def parse(path):
    slug = path.stem
    topic, sub, card, field = slug, None, None, None
    cards = []
    for line in path.read_text().splitlines():
        if line.startswith("# "):
            topic = line[2:].strip()
        elif line.startswith("## "):
            sub = line[3:].strip()
        elif m := re.match(r"(Q|A|Why|Flip|Staff):\s?(.*)", line):
            field = m.group(1)
            if field == "Q":
                card = {"sub": sub, "Q": "", "A": "", "Why": "", "Flip": "", "Staff": ""}
                cards.append(card)
            card[field] = m.group(2)
        elif card is not None and field:
            card[field] += "\n" + line
    return topic, [{k: v.strip() if isinstance(v, str) else v for k, v in c.items()} for c in cards]


def back(card):
    out = card["A"]
    if card["Why"]:
        out += "\n\n**Why:** " + card["Why"]
    if card["Flip"]:
        out += "\n\n**Flip it when:** " + card["Flip"]
    if card["Staff"]:
        out += "\n\n*Staff: " + card["Staff"] + "*"
    return out


def norm(text):
    return "\n".join(l.rstrip() for l in text.strip().splitlines() if l.strip())


def space(*args):
    r = subprocess.run(["space", "--no-color", *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"space {' '.join(args)} failed:\n{r.stderr or r.stdout}")
    return r.stdout


def new_id(out):
    m = re.search(r"\(([0-9a-f-]{36})\)", out)
    if not m:
        sys.exit(f"could not find an ID in:\n{out}")
    return m.group(1)


def sync(path, ids, dry, prune):
    slug = path.stem
    topic, cards = parse(path)
    entry = ids.setdefault(slug, {"deck": None})
    if not entry["deck"]:
        print(f"  create deck {DECK_PREFIX}{topic}")
        if dry:
            existing = {}
        else:
            entry["deck"] = new_id(space("deck", "create", DECK_PREFIX + topic))
    if entry["deck"]:
        exported = json.loads(space("deck", "export", entry["deck"]))["cards"]
        existing = {norm(c["front"]): c for c in exported}
    seen = set()
    counts = {"new": 0, "edit": 0, "same": 0}
    for card in cards:
        key = norm(card["Q"])
        seen.add(key)
        body = back(card)
        if key in existing:
            if norm(existing[key]["back"]) == norm(body):
                counts["same"] += 1
                continue
            counts["edit"] += 1
            print(f"  edit  {card['Q'][:70]}")
            if not dry:
                space("card", "edit", existing[key]["id"], "--back", body)
            continue
        counts["new"] += 1
        print(f"  new   [{card['sub']}] {card['Q'][:60]}")
        if dry:
            continue
        space("card", "create", entry["deck"], "--front", card["Q"], "--back", body)
    orphans = [c for k, c in existing.items() if k not in seen]
    for c in orphans:
        print(f"  {'delete' if prune else 'orphan'} {c['front'][:70]}")
        if prune and not dry:
            space("card", "delete", c["id"])
    print(f"{slug}: {counts['new']} new, {counts['edit']} edited, {counts['same']} unchanged, {len(orphans)} orphaned")


def main():
    args = sys.argv[1:]
    dry, prune = "--dry-run" in args, "--prune" in args
    slugs = [a for a in args if not a.startswith("--")]
    ids = json.loads(IDS.read_text()) if IDS.exists() else {}
    paths = sorted((HERE / "cards").glob("*.md"))
    if slugs:
        paths = [p for p in paths if p.stem in slugs]
    try:
        for p in paths:
            sync(p, ids, dry, prune)
    finally:
        if not dry:
            IDS.write_text(json.dumps(ids, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
