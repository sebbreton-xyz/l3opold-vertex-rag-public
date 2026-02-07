#!/usr/bin/env python3
import argparse
import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode
import urllib.request

EUTILS_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
OAI_GETRECORD = "https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/"

DEFAULT_UA = "l3opold-poc/0.1 (contact: github.com/sebbreton-xyz)"

def http_get(url: str, headers: dict | None = None, timeout: int = 60) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception:
        return 0, b""

def esearch_ids(term: str, retmax: int) -> list[str]:
    params = {
        "db": "pmc",
        "term": term,
        "retmode": "json",
        "retmax": str(retmax),
    }
    url = f"{EUTILS_ESEARCH}?{urlencode(params)}"
    code, body = http_get(url, headers={"User-Agent": DEFAULT_UA, "Accept": "application/json"})
    if code != 200:
        raise RuntimeError(f"esearch failed: HTTP {code}\n{body[:2000]!r}")
    data = json.loads(body.decode("utf-8", errors="replace"))
    return data["esearchresult"]["idlist"]

def oai_getrecord(aid: str) -> tuple[int, bytes]:
    params = {
        "verb": "GetRecord",
        "identifier": f"oai:pubmedcentral.nih.gov:{aid}",
        "metadataPrefix": "pmc",
    }
    url = f"{OAI_GETRECORD}?{urlencode(params)}"
    headers = {"User-Agent": DEFAULT_UA, "Accept": "application/xml"}
    return http_get(url, headers=headers)

def is_html_429(payload: bytes) -> bool:
    head = payload[:500].lower()
    return b"429" in head and b"too many requests" in head or b"<!doctype html" in head

def is_oai_xml(payload: bytes) -> bool:
    # Basic signal: OAI-PMH envelope
    return b"<OAI-PMH" in payload[:5000]

def main():
    ap = argparse.ArgumentParser(description="Fetch PMC OAI-PMH XML records (metadataPrefix=pmc) into data/raw/pmc_xml.")
    ap.add_argument("--term", help="E-utilities esearch term (db=pmc). If provided, will generate IDs.")
    ap.add_argument("--ids-file", help="Path to file with one AID per line (from esearch idlist).")
    ap.add_argument("--retmax", type=int, default=100, help="How many IDs to request from esearch (if --term used).")
    ap.add_argument("--out-dir", default="data/raw/pmc_xml", help="Output directory for XML files.")
    ap.add_argument("--sleep", type=float, default=8.0, help="Sleep seconds between requests.")
    ap.add_argument("--retry", type=int, default=3, help="Retries per AID on non-200 or invalid payload.")
    ap.add_argument("--backoff", type=float, default=20.0, help="Backoff seconds on retry (e.g. 429).")
    ap.add_argument("--limit", type=int, default=0, help="Optional limit of IDs processed (0 = no limit).")
    args = ap.parse_args()

    if not args.term and not args.ids_file:
        raise SystemExit("Provide either --term or --ids-file")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.term:
        ids = esearch_ids(args.term, args.retmax)
    else:
        ids = [ln.strip() for ln in Path(args.ids_file).read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]

    if args.limit and args.limit > 0:
        ids = ids[:args.limit]

    rejected = []
    downloaded = 0

    for idx, aid in enumerate(ids, start=1):
        out_path = out_dir / f"PMC{aid}.xml"
        if out_path.exists() and out_path.stat().st_size > 0:
            continue

        ok = False
        for attempt in range(1, args.retry + 1):
            code, payload = oai_getrecord(aid)

            if code == 200 and is_oai_xml(payload) and not is_html_429(payload):
                out_path.write_bytes(payload)
                downloaded += 1
                ok = True
                print(f"[{idx}/{len(ids)}] OK {aid} ({len(payload)} bytes)")
                break

            # retry path
            if out_path.exists():
                out_path.unlink(missing_ok=True)

            print(f"[{idx}/{len(ids)}] FAIL {aid} (HTTP {code}) attempt {attempt}/{args.retry}")
            time.sleep(args.backoff)

        if not ok:
            rejected.append(aid)

        time.sleep(args.sleep)

    # Write rejected list
    if rejected:
        rej_path = Path("data/tmp/rejected_aids.txt")
        rej_path.parent.mkdir(parents=True, exist_ok=True)
        rej_path.write_text("\n".join(rejected) + "\n", encoding="utf-8")
        print(f"Rejected: {len(rejected)} -> {rej_path}")

    print(f"Downloaded new files: {downloaded}")
    print(f"Out dir: {out_dir}")

if __name__ == "__main__":
    main()
