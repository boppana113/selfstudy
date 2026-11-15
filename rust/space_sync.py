"""Sync rust/cards/*.md into Space as "Rust · <Topic>" decks.

Same card format and behavior as system-design/space_sync.py (which this reuses);
deck IDs live in rust/space-ids.json.

Usage: python3 rust/space_sync.py [slug ...] [--dry-run] [--prune]
"""

import importlib.util
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("sd_sync", HERE.parent / "system-design" / "space_sync.py")
sd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd)

sd.DECK_PREFIX = "Rust · "
sd.HERE = HERE
sd.IDS = HERE / "space-ids.json"

if __name__ == "__main__":
    sd.main()
