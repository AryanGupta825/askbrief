"""
CLI adapter.

Usage:
    python -m parser --input briefs/F03.txt --out out/F03.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import parse_brief, ParseError


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse a hiring brief into structured criteria.")
    ap.add_argument("--input", required=True, help="Path to a brief .txt file")
    ap.add_argument("--out", required=True, help="Path to write the resulting JSON")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.out)

    if not in_path.exists():
        print(f"Input file not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    text = in_path.read_text(encoding="utf-8")
    brief_id = in_path.stem

    try:
        result = parse_brief(text, brief_id=brief_id)
    except ParseError as e:
        print(f"Failed to parse {in_path}: {e}", file=sys.stderr)
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
