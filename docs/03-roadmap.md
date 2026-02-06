## 🗺️ Roadmap

<div style="display: flex; flex-wrap: wrap; gap: 16px;">

  <!-- Phase 1 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 1 — Public Demo (Grounding + Governance) ✅</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Status: completed (public repo ready)
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [x] Public corpus <code>corpus/sample/</code> (governance + playbook)</li>
      <li>- [x] Strict rules: JSON schema, banned terms, fixed final line</li>
      <li>- [x] “current vs obsolete” trap + precedence demonstration</li>
      <li>- [x] Verifiable citations: <code>ALLOWED_SOURCES</code> (real file paths)</li>
      <li>- [x] Demo scripts: <code>demo_playbook_local</code> (+ optional GCS mode)</li>
      <li>- [ ] Architecture docs + diagrams (Step 1 + Step 2 target)</li>
    </ul>
  </div>

  <!-- Phase 2 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 2 — Indexing (Chunking + Embeddings)</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: build a reusable index (artifacts) from the corpus
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] Define chunking strategy (size, overlap, doc types)</li>
      <li>- [ ] Generate embeddings (Vertex embeddings or equivalent)</li>
      <li>- [ ] Persist artifacts: chunks + metadata (<code>source</code>, <code>chunk_id</code>, <code>status</code>)</li>
      <li>- [ ] Build vector index (local: FAISS/Chroma) or (cloud: Vertex Vector Search)</li>
      <li>- [ ] Add <code>scripts/index_corpus.py</code> (idempotent, rerunnable)</li>
      <li>- [ ] Repro flow: <code>make index</code> → artifacts</li>
    </ul>
  </div>

  <!-- Phase 3 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 3 — Retrieval (Top-K) + Chunk-level Citations</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: prove the “with/without retrieval” difference and ground citations on chunks
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] Module <code>rag/retriever.py</code>: embed question → top-k chunks</li>
      <li>- [ ] Compact prompt: governance + top-k chunks (no full-corpus stuffing)</li>
      <li>- [ ] JSON output: <code>sources</code> = chunk ids/paths actually used</li>
      <li>- [ ] Compare modes: <code>MODE=stuffing</code> vs <code>MODE=retrieval</code></li>
      <li>- [ ] Tests: “current/obsolete conflict” + “banned terms”</li>
      <li>- [ ] Saved outputs in <code>examples/</code> (proof artifacts)</li>
    </ul>
  </div>

  <!-- Phase 4 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 4 — FastAPI (Minimal Backend)</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: expose the pipeline as an API (ready to plug into a UI)
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] <code>POST /ask</code> endpoint (question, mode, top_k)</li>
      <li>- [ ] Load index on startup (warm) + controlled caching</li>
      <li>- [ ] Stable response schema: <code>answer</code>, <code>sources</code>, <code>tags</code>, <code>final_line</code></li>
      <li>- [ ] Minimal logging (request_id), no sensitive payloads</li>
      <li>- [ ] Env-based config (<code>PROJECT_ID</code>, <code>REGION</code>, <code>MODEL</code>)</li>
      <li>- [ ] Docs: <code>curl</code> examples + OpenAPI</li>
    </ul>
  </div>

  <!-- Phase 5 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 5 — Zen UI (Minimal Front)</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: make the demo usable for non-devs (question → sourced answer)
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] Text input + “Ask” button</li>
      <li>- [ ] Clear rendering: answer + sources + tags</li>
      <li>- [ ] Toggle: stuffing vs retrieval (side-by-side comparison)</li>
      <li>- [ ] Presets: example questions (one click)</li>
      <li>- [ ] “Debug mode”: show raw JSON (optional)</li>
      <li>- [ ] Simple deploy (optional): Cloud Run / Vercel + proxy</li>
    </ul>
  </div>

  <!-- Phase 6 -->
  <div style="flex: 1; min-width: 280px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;">
    <h3 style="margin-top: 0;">Phase 6 — Hardening (Production-minded, optional)</h3>
    <p style="margin: 6px 0 12px; color: #6b7280;">
      Goal: demonstrate “prod” instincts
    </p>
    <ul style="list-style: none; padding-left: 0; margin: 0;">
      <li>- [ ] API auth + rate limiting</li>
      <li>- [ ] Budgets/alerts + quotas + cost protections</li>
      <li>- [ ] Observability (structured logs, metrics, traces)</li>
      <li>- [ ] Environment separation (dev/stage/prod)</li>
      <li>- [ ] Secret management (Secret Manager) + least-privilege IAM</li>
      <li>- [ ] “Compliance-ready” documentation (principles + checklists)</li>
    </ul>
  </div>

</div>

