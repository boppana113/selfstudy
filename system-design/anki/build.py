"""Build an Anki import file from cards/*.md.

Card file format (one file per topic slug):

    # Kafka                      <- topic deck name
    ## Consumer groups           <- subtopic deck name
    Q: question (can span lines, ``` blocks allowed)
    A: answer
    Staff: optional stretch line, shown under the answer

Writes system-design.txt next to this script. Import it in Anki with
File > Import, and set "Existing notes" to Update. Each card's GUID is a
hash of its topic and question, so re-importing updates answers in place.
Changing a question makes a new card; delete the old one in Anki.
"""

import hashlib
import html
import re
from pathlib import Path

ROOT_DECK = "System Design"
HERE = Path(__file__).parent
OUT = HERE / "system-design.txt"


def to_html(text):
    parts = re.split(r"```\w*\n?(.*?)```", text.strip(), flags=re.S)
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            out.append("<pre>" + html.escape(part.rstrip()) + "</pre>")
            continue
        part = html.escape(part.strip())
        part = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", part)
        part = re.sub(r"`(.+?)`", r"<code>\1</code>", part)
        out.append(part.replace("\n", "<br>"))
    return "".join(p for p in out if p)


def parse(path):
    slug = path.stem
    topic, sub, card, field = slug, None, None, None
    cards = []
    for line in path.read_text().splitlines():
        if line.startswith("# "):
            topic = line[2:].strip()
        elif line.startswith("## "):
            sub = line[3:].strip()
        elif m := re.match(r"(Q|A|Staff):\s?(.*)", line):
            field = m.group(1)
            if field == "Q":
                card = {"slug": slug, "topic": topic, "sub": sub, "Q": "", "A": "", "Staff": ""}
                cards.append(card)
            card[field] = m.group(2)
        elif card is not None and field:
            card[field] += "\n" + line
    return cards


def row(card):
    deck = "::".join(p for p in (ROOT_DECK, card["topic"], card["sub"]) if p)
    guid = hashlib.sha1(f'{card["slug"]}|{card["Q"].strip()}'.encode()).hexdigest()[:16]
    back = to_html(card["A"])
    if card["Staff"].strip():
        back += '<br><br><i style="opacity:.7">Staff: ' + to_html(card["Staff"]) + "</i>"
    fields = [deck, guid, to_html(card["Q"]), back, f'sd::{card["slug"]}']
    return "\t".join('"' + f.replace('"', '""') + '"' for f in fields)


def main():
    cards = [c for p in sorted((HERE / "cards").glob("*.md")) for c in parse(p)]
    header = [
        "#separator:Tab",
        "#html:true",
        "#notetype:Basic",
        "#deck column:1",
        "#guid column:2",
        "#tags column:5",
    ]
    OUT.write_text("\n".join(header + [row(c) for c in cards]) + "\n")
    print(f"{len(cards)} cards -> {OUT}")


if __name__ == "__main__":
    main()
