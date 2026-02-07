#!/usr/bin/env python3
"""
Sample chunks for manual inspection.

To adapt:
- --n (sample size)
- --section filter (focus abstract/methods/etc.)
"""

from __future__ import annotations
import argparse
import json
import random
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="artifacts/chunks.jsonl")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--section", default="", help="Optional filter: only chunks with this section")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    path = Path(args.input)
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            if args.section and o.get("section") != args.section:
                continue
            items.append(o)

    random.seed(args.seed)
    sample = random.sample(items, k=min(args.n, len(items)))

    for i, o in enumerate(sample, start=1):
        print("=" * 80)
        print(f"[{i}] {o.get('chunk_id')}  section={o.get('section')}  doc={o.get('doc_id')}")
        print(o.get("text", "").strip()[:1200])  # truncate display


if __name__ == "__main__":
    main()
