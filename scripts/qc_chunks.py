#!/usr/bin/env python3
"""
QC for chunks.jsonl

To adapt for your use, consider:
- --min-len / --max-len thresholds (based on your chunking strategy)
- allowed sections (if you want to enforce a set)
- what counts as "empty" (strip vs not)
- failing rules: whether empty/duplicates should hard-fail (exit != 0)
"""

from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
import statistics
import sys


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield i, json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {i}: {e}") from e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="artifacts/chunks.jsonl", help="Path to chunks.jsonl")
    ap.add_argument("--report", default="", help="Optional: write a JSON report to this path")
    ap.add_argument("--min-len", type=int, default=50, help="Warn if chunk text length < min-len (chars)")
    ap.add_argument("--max-len", type=int, default=5000, help="Warn if chunk text length > max-len (chars)")
    ap.add_argument("--fail-on-dup", action="store_true", help="Exit with non-zero code if duplicate chunk_id found")
    ap.add_argument("--fail-on-empty", action="store_true", help="Exit with non-zero code if empty text found")
    args = ap.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"[ERR] Not found: {path}", file=sys.stderr)
        return 2

    n = 0
    empty = 0
    dup = 0
    seen_ids = set()
    sections = Counter()
    lens = []

    too_short = 0
    too_long = 0

    for _, o in load_jsonl(path):
        n += 1
        cid = o.get("chunk_id")
        if not cid:
            # treat missing chunk_id as a hard issue
            dup += 1
        else:
            if cid in seen_ids:
                dup += 1
            seen_ids.add(cid)

        section = o.get("section", "?")
        sections[section] += 1

        text = (o.get("text") or "")
        t = text.strip()
        if not t:
            empty += 1

        L = len(t)
        lens.append(L)
        if L and L < args.min_len:
            too_short += 1
        if L > args.max_len:
            too_long += 1

    lens_sorted = sorted(lens) if lens else [0]
    median = statistics.median(lens_sorted)
    p90 = lens_sorted[int(0.90 * (len(lens_sorted) - 1))]

    report = {
        "input": str(path),
        "lines": n,
        "empty_text": empty,
        "duplicate_chunk_id": dup,
        "sections": dict(sections.most_common()),
        "length_chars": {
            "min": lens_sorted[0],
            "median": median,
            "p90": p90,
            "max": lens_sorted[-1],
            "too_short": too_short,
            "too_long": too_long,
            "min_len_threshold": args.min_len,
            "max_len_threshold": args.max_len,
        },
    }

    # Print human summary
    print("== QC chunks ==")
    print(f"Input: {path}")
    print(f"Lines: {n}")
    print(f"Empty text: {empty}")
    print(f"Duplicate chunk_id: {dup}")
    print(f"Len chars: min={report['length_chars']['min']} median={median} p90={p90} max={report['length_chars']['max']}")
    print(f"Too short (<{args.min_len}): {too_short}")
    print(f"Too long  (>{args.max_len}): {too_long}")
    print("Top sections:")
    for k, v in sections.most_common(12):
        print(f"  - {k}: {v}")

    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Report written: {out}")

    # Exit policy (for CI / Makefile)
    exit_code = 0
    if args.fail_on_empty and empty > 0:
        exit_code = 1
    if args.fail_on_dup and dup > 0:
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
