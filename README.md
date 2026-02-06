# RAG Demo Kit (Vertex AI) — Public Sample Corpus

This repository is a public, sanitized demo kit designed to showcase the building blocks of a private RAG pipeline on **Google Cloud / Vertex AI**.

It focuses on:
- **strict output constraints** (schema + banned terms + fixed final line)
- **version precedence** (current vs obsolete, conflict resolution)
- **source-backed answers** (verifiable file paths as citations)
- **reproducibility** (clone + run)

> Note: the current demo stage uses **document grounding (local-first)** without vector retrieval.  
> A full **chunking / embeddings / top-k retrieval** pipeline is part of the roadmap.

---

## Why this repo exists

This repository is a public, educational (intentionally limited) version of a private RAG project.  
The real/private corpus is not included for confidentiality and IP reasons.

A minimal sample corpus under `corpus/sample/` is provided to reproduce the core behavior:
- governance rules (format + precedence + banned terms)
- source-backed answers using **real file paths**
- deterministic “current > obsolete” precedence in conflicts

Production concerns (security hardening, deployment, observability, compliance) are out of scope for this public demo.

---

## Contents

- `corpus/sample/` — governance + playbook documents (public toy corpus)
- `scripts/` — demo scripts (Vertex AI call + JSON output)
- `docs/` — documentation (architecture + roadmap)

---

## Quickstart (Cloud Shell)

### 0) Prerequisites
- Python 3
- A Google Cloud project with **Vertex AI enabled**
- Working **Application Default Credentials (ADC)**

### 1) Authenticate (ADC) — recommended isolated config
```bash
export CLOUDSDK_CONFIG="$HOME/.config/gcloud-demo"
gcloud auth application-default login --no-launch-browser
gcloud auth application-default set-quota-project <YOUR_PROJECT_ID>
export GOOGLE_APPLICATION_CREDENTIALS="$CLOUDSDK_CONFIG/application_default_credentials.json"
```

### 2) Run the demo (local-first)
```bash
export PROJECT_ID="<YOUR_PROJECT_ID>"
export REGION="europe-west1"
python3 -m scripts.demo_playbook_local
```

### 3) Example: version precedence (current vs obsolete)
```bash
export QUESTION="If current and obsolete logging policies conflict, which one should be followed and why? Cite sources."
python3 -m scripts.demo_playbook_local
```

## Security hygiene (do not commit secrets)

Do not commit:

- API keys, tokens, service accounts (*.json)

- .env files

- private corpora or non-public documents