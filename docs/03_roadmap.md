* **Phase 1** : Public Demo (Governance + Grounding) ✅
* **Phase 2** : Medical Corpus (PMC OA acquisition + préparation) ✅
* **Phase 3A** : Vertex RAG Engine (Managed) ✅
* **Phase 3B** : FAISS Indexing (Open-source) ⏳
* **Phase 4A** : Vertex Retrieval + Audit ✅
* **Phase 4B** : FAISS Retrieval + chunk-level citations ⏳
* **Phase 5** : FastAPI ⏳
* **Phase 6** : UI ⏳
* **Phase 7** : Hardening ⏳

---

# Roadmap

## Phase 1 — Public Demo (Grounding + Governance)

Status: completed (public repo ready) — domain-agnostic foundation

* [x] Public corpus
* [x] Strict rules: JSON schema, banned terms, fixed final line
* [x] “current vs obsolete” trap + precedence demonstration
* [x] Verifiable citations: `ALLOWED_SOURCES` (real file paths)
* [x] Demo scripts
* [x] Architecture docs + diagrams

---

## Phase 2 — Medical Corpus (PMC OA via OAI-PMH) (Core)

Goal: build an English, sourceable, structured corpus ready for indexing (Open Access)

* [x] Find PMCIDs with an “adverse events / pharmacovigilance” query
* [x] Download full-text JATS XML via OAI-PMH
* [x] Chunk extraction + sanity checks
* [x] Pre-embeddings QC (integrity + sampling) → run logs
* [x] Export docs for Vertex RAG Engine
* [x] Upload to GCS (EW4)
* [ ] Normalize & store
* [ ] Metadata index
* [ ] “English only” filter 

---

## Phase 3A — Vertex RAG Engine (Managed)

Status: completed — corpus / import / retrieve+generate with audit artifacts

* [x] Region aligned with bucket
* [x] Create RAG corpus on Vertex
* [x] Import docs from GCS prefix 
* [x] Config captured
* [x] Script: `vertex_rag_create_import.py` (writes run artifacts)
* [x] Run artifacts: `vertex_rag_corpus.txt` + `vertex_rag_import_meta.json`
* [x] Script: `vertex_rag_ask.py` (retrieve+generate)
* [x] Prints answer + sources (URIs) + excerpts
* [x] Saves JSON audit artifacts

---

## Phase 3B — FAISS Indexing (Open-source)

Goal: produce a local FAISS index / reproducible artifacts

* [x] Artifact already available: `artifacts/chunks.jsonl` (4,417 chunks)
* [ ] Section-based chunking strategy (Abstract/Methods/Results/Discussion) + max size per chunk
* [ ] Generate embeddings
* [ ] Vertex embeddings (benchmark / comparison)
* [ ] Artifacts: `artifacts/embeddings.npy`, `artifacts/index.faiss`
* [ ] Idempotent script: `scripts/index_corpus.py` (rerunnable, stable)
* [ ] Repro command: `make index` → artifacts

---

## Phase 4 — Retrieval (Local pipeline) + Chunk-level Citations (FAISS)

Goal: local retriever (FAISS) + precise chunk IDs (PMCID/section/chunk)

* [ ] `rag/retriever.py` switch: `retriever=faiss` (default) / `retriever=vertex_vector_search`
* [ ] Pipeline: embed question → top-k chunks → compact prompt (governance + chunks)
* [ ] JSON output unchanged: `sources` = chunk ids + pmcid + section (+ offsets if available)
* [ ] Comparison remains: `MODE=stuffing` vs `MODE=retrieval`
* [ ] Strong “medical OA” demo: retrieval cites Methods/Results (fewer hallucinations)
* [ ] Save outputs

---

## Phase 5 — FastAPI (Minimal Backend)

Goal: expose the pipeline via API (ready to plug into a UI) + simple filters

* [x] `POST /ask` endpoint 
* [x] Useful params
* [ ] Collection param
* [ ] Load index on startup (warm) + controlled caching
* [ ] Stable response schema
* [x] Docs: `curl` examples + OpenAPI

---

## Phase 6 — UI (Minimal Front)

Goal: make the demo usable for non-devs

* [ ] Text input + “Ask” button
* [ ] Clear rendering: answer + sources + tags (and sections)
* [ ] Toggle: stuffing vs retrieval (comparison)
* [ ] Presets: example questions (1 click)
* [ ] Medical OA preset: “Summarize adverse events of drug X from retrieved sources.”
* [ ] “Debug mode”: show raw JSON

---

## Phase 7 — Hardening (Production-minded)

Goal: show production instincts (without claiming HIPAA compliance here)

* [ ] Minimal logging 
* [ ] Budget guardrails
* [ ] API auth + rate limiting
* [ ] Observability 
* [ ] Secret management + least-privilege IAM
* [ ] Clear note: Open Access corpus, no PHI (patient data)

---

