## Architecture evolution (3 steps)

These three diagrams summarize how my approach is evolving, from a minimal prototype to a traceable RAG architecture. 
- I started with an simple MVP: grounded generation steered by a small private corpus stored on Cloud Storage. 
- Then I built a local “toy” variant centered on a prompt-engine (rules, forbidden patterns, output formats) to quickly test control and reproducibility. 
- Finally, the third diagram describes the target: a full RAG pipeline on Vertex AI (chunking → embeddings → retrieval → citations), designed to increase reliability, traceability, and the ability to justify outputs — a key requirement for higher-stakes use cases.

### Figure 1 — MVP (grounded generation, pre-RAG)


```text
[Canon .md (local authoring)]
        |
        |  upload (gsutil cp)
        v
[Private GCS bucket]
        |
        |  runtime read (gsutil cat / Storage API)
        v
[Docs concatenation → prompt stuffing]
        |
        v
[Gemini on Vertex (generate_content)]
        |
        v
[Text output (studio log / post)]
```
*(1) MVP — Grounded generation via GCS (no index, no retrieval)*
**Note:** Canon stocké sur GCS, lu à l’exécution et injecté dans le prompt (“prompt stuffing”) avant génération.


### Figure 2 — Local toy prompt-engine (reproducible demo)

```text
[Terminal]  python3 -m scripts.demo_playbook_local
    |
    v
[demo_playbook_local.py]
    |
    |--(1) init_vertex()
    |        |
    |        +--> vertexai.init(project=PROJECT_ID, location=REGION)
    |
    |--(2) load_local_docs("corpus/sample")
    |        |
    |        +--> reads the. md/. txt (governance + playbook)
    |        +--> create a Doc list (source=path, text=content)
    |
    |--(3) question = $QUESTION (otherwise question by default)
    |
    |--(4) build_prompt(question, docs)
    |        |
    |        +--> make a PROMPT text that contains :
    |              - strict rules (JSON, current>obsolete, banned)
    |              - ALLOWED_SOURCES (exact list of paths)
    |              - DOCUMENTS (all the concatenated content)
    |
    |--(5) generate(prompt)
    |        |
    |        +--> Vertex AI (Gemini) via GenerativeModel.generate_content(prompt)
    |
    |--(6) pretty_print_json_or_raw(resp.text)
             |
             +--> displays the JSON (indented)
```
*(2) Demo — Local “toy corpus” prompt-engine (no index, no retrieval)*
**Note:** Corpus d’exemple local chargé et concaténé dans un prompt strict (règles/format/interdits) pour produire une sortie contrôlée.

### Figure 3 — Target architecture (full RAG on Vertex) ###

```text
[Medical / domain sources (PDF/MD/HTML)]
        |
        |  ingest + normalize (+ de-id if needed)
        v
[Private GCS bucket]
        |
        |  import into Vertex RAG Corpus
        |  (chunking_config + embeddings)
        v
[Vertex RAG Corpus + Vector Index]
        |
        |  query → retrieval (top-k + filters)
        v
[Relevant chunks + metadata]
(source, page/section, score)
        |
        |  context injection + grounding tool
        v
[LLM (Gemini / other) on Vertex]
        |
        v
[Answer + citations/sources + traceability]
```
*(3) Target — Full RAG pipeline on Vertex (chunking → embeddings → retrieval → citations)*
**Note:** Ingestion + index vectoriel + retrieval top-k, puis génération LLM avec sources/citations traçables.

