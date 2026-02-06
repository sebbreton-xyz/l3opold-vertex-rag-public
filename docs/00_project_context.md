*Artificial intelligence doesn’t do things instead of us; it follows human instructions. That is where the real leverage lives — this is the starting paradigm.*

## Project origin (why this started)

This repository originated as an attempt to design an **AI artist-agent**, **L3opold**, able to produce constrained prose from a deliberately defined corpus: rules, lexicon, style grammar, and versioned “laws.” The intention was to treat language generation as a **constraint engine** rather than a free-form chatbot.

![Vertex MVP run proof](assets/screenshots/Studio_log_bloc.png)
*Figure — Vertex AI text generation grounded on a small curated corpus (pre-RAG, no vector index yet), aligned with persona constraints.*

What surprised me here is the *sharpness* of the language: it feels *chiseled* by constraints rather than “averaged” by a generic chatbot.  
This MVP is intentionally simple: it demonstrates **grounded generation** (the model is steered by explicit, curated texts) before moving to a full RAG pipeline (chunking → embeddings → retrieval → citations).

This kind of control is exactly what I want to study further for higher-stakes domains: **more traceable steering**, and eventually **retrieval-backed answers**.



## Why Vertex AI (and why this is still transferable)

The initial plan was to evolve toward an **open-source RAG stack** (e.g., a self-hosted LLM + embeddings + vector store) to keep full control over infrastructure and portability. However, I chose to prototype on **Google Cloud Vertex AI** to gain hands-on experience with a production-grade environment and modern managed RAG components.

This work is meant to be **transposable**: the long-term goal is to re-implement the same pipeline on an open-source stack, in order to clearly identify the **provider-agnostic fundamentals** RAG pipeline and agent orchestration layer versus the **vendor-specific integration details** (authentication, managed services, deployment primitives).
