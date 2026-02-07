````md
## Run log — Pre-embeddings QC (chunks)

**Date:** 2026-02-07  
**Stage:** Dataset validation before embeddings / indexing  
**Artifact:** `artifacts/chunks.jsonl` (70 docs → 4,417 chunks)

### Commands
```bash
python scripts/qc_chunks.py --input artifacts/chunks.jsonl --report outputs/runs/2026-02-07/qc_chunks.json
python scripts/sample_chunks.py --n 10
````

### QC summary (`qc_chunks.py`)

* **Chunks:** 4,417
* **Empty text:** 0
* **Duplicate `chunk_id`:** 0
* **Lengths (chars):** min=35, median≈1200, p90≈1200, max≈1200
* **Too short (<50):** 2
* **Too long (>5000):** 0
* **Sections:** body=4,202 · abstract=145 · title=70
* **Report:** `outputs/runs/2026-02-07/qc_chunks.json`

### Interpretation

* **Integrity OK** (zero empty chunks, zero duplicate IDs).
* **Coverage looks plausible:** ~1 title per doc, abstracts sometimes split, body is the majority.
* **Chunking is stable** around ~1200 chars (suitable for embeddings).
* **Very short chunks** (<50) flagged → inspected below.

### Short chunks inspection

Both short chunks are **titles** (expected; no filtering needed):

* `12824447:title:0` — "A Case of Drug‐Induced Pancreatitis" (35 chars)
* `12858747:title:0` — "How is AI developing in pharmacovigilance?" (42 chars)

### Results — Manual check (`sample_chunks.py`)

Random sample of 10 chunks:

* readable, coherent scientific content (methods, tables, results)
* no obvious XML noise
* sentence boundaries may be cut (expected with raw chunking)

### Decision

The chunked dataset is considered **OK** to proceed with **embeddings → FAISS**.

```
```
