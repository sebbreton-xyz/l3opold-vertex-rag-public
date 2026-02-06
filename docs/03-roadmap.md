## 🗺️ Roadmap

<div style="display: flex; flex-wrap: wrap; gap: 16px;">

<!-- Stade 1 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 1 — Public Demo (Grounding + Governance) ✅</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Status: completed (public repo ready) — domain-agnostic foundation
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [x] Public corpus <code>corpus/sample/</code> (governance + playbook)</li>
      <li>- [x] Strict rules: JSON schema, banned terms, fixed final line</li>
      <li>- [x] “current vs obsolete” trap + precedence demonstration</li>
      <li>- [x] Verifiable citations: <code>ALLOWED_SOURCES</code> (real file paths)</li>
      <li>- [x] Demo scripts: <code>demo_playbook_local</code> (+ optional GCS mode)</li>
      <li>- [x] Architecture docs + diagrams (Step 1 + Step 2 target)</li>
    </ul>
  </div>

<!-- Stade 2 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 1.5 — Medical Corpus (PMC OA via OAI-PMH)</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: build an English, sourceable, structured corpus ready for chunking (Open Access)
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] Find PMCIDs (E-utilities <code>esearch</code> on <code>pmc</code>) with an “adverse events / pharmacovigilance” query</li>
      <li>- [ ] Download full-text JATS XML via OAI-PMH <code>GetRecord</code> (<code>metadataPrefix=pmc</code>, <code>set=pmc-open</code>)</li>
      <li>- [ ] Normalize & store: <code>data/raw/pmc_xml/PMCID.xml</code></li>
      <li>- [ ] Metadata index: <code>data/meta/articles.jsonl</code> (pmcid, title, year, journal, license, url)</li>
      <li>- [ ] “English only” filter (lang if available + fallback heuristic)</li>
    </ul>
  </div>

<!-- Stade 3 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 2 — Indexing (Chunking + Embeddings) — Hybrid</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: produce a local FAISS index + reproducible artifacts (Vertex embeddings optional for comparison)
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] Section-based chunking strategy (Abstract/Methods/Results/Discussion) + max size per chunk</li>
      <li>- [ ] Generate embeddings (default: open-source <code>sentence-transformers</code> in batch)</li>
      <li>- [ ] Optional: Vertex embeddings (benchmark / comparison)</li>
      <li>- [ ] Artifacts: <code>artifacts/chunks.jsonl</code>, <code>artifacts/embeddings.npy</code>, <code>artifacts/index.faiss</code></li>
      <li>- [ ] Idempotent script: <code>scripts/index_corpus.py</code> (rerunnable, stable)</li>
      <li>- [ ] Repro command: <code>make index</code> → artifacts</li>
    </ul>
  </div>

<!-- Stade 4 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 3 — Retrieval (Top-K) + Chunk-level Citations</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: prove the “with/without retrieval” difference and cite precisely (PMCID/section/chunk)
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] <code>rag/retriever.py</code> switch: <code>retriever=faiss</code> (default) / <code>retriever=vertex_vector_search</code> (later)</li>
      <li>- [ ] Pipeline: embed question → top-k chunks → compact prompt (governance + chunks)</li>
      <li>- [ ] JSON output unchanged: <code>sources</code> = chunk ids + pmcid + section (+ offsets if available)</li>
      <li>- [ ] Comparison remains: <code>MODE=stuffing</code> vs <code>MODE=retrieval</code></li>
      <li>- [ ] Strong “medical OA” demo: retrieval cites Methods/Results (fewer hallucinations)</li>
      <li>- [ ] Save outputs in <code>examples/</code> (proof artifacts)</li>
    </ul>
  </div>

<!-- Stade 5 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 4 — FastAPI (Minimal Backend)</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: expose the pipeline via API (ready to plug into a UI) + simple filters
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] <code>POST /ask</code> endpoint (question, mode, top_k)</li>
      <li>- [ ] Useful params: <code>filters</code> (year_from, journal, study_type if extracted)</li>
      <li>- [ ] Collection param: <code>collection=pmc_adverse_events_v1</code></li>
      <li>- [ ] Load index on startup (warm) + controlled caching</li>
      <li>- [ ] Stable response schema: <code>answer</code>, <code>sources</code>, <code>tags</code>, <code>final_line</code></li>
      <li>- [ ] Docs: <code>curl</code> examples + OpenAPI</li>
    </ul>
  </div>

<!-- Stade 6 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 5 — Zen UI (Minimal Front)</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: make the demo usable for non-devs (question → answer + sources)
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] Text input + “Ask” button</li>
      <li>- [ ] Clear rendering: answer + sources + tags (and sections)</li>
      <li>- [ ] Toggle: stuffing vs retrieval (comparison)</li>
      <li>- [ ] Presets: example questions (1 click)</li>
      <li>- [ ] Medical OA preset: “Summarize adverse events of drug X from retrieved sources.”</li>
      <li>- [ ] “Debug mode”: show raw JSON (optional)</li>
    </ul>
  </div>

<!-- Stade 7 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 6 — Hardening (Production-minded, optional)</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: show production instincts (without claiming HIPAA compliance here)
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] Minimal logging (no sensitive payloads) + request_id</li>
      <li>- [ ] Budget guardrails (top_k, max_output_tokens, caching) + alerts/quotas</li>
      <li>- [ ] API auth + rate limiting</li>
      <li>- [ ] Observability (structured logs, metrics, traces)</li>
      <li>- [ ] Secret management (Secret Manager) + least-privilege IAM</li>
      <li>- [ ] Clear note: Open Access corpus, no PHI (patient data)</li>
    </ul>
  </div>

</div>
