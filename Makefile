.PHONY: help fetch chunks qc sample

help:
	@echo "Targets:"
	@echo "  make fetch   TERM='...' RETMAX=100 SLEEP=8 RETRY=3 BACKOFF=20"
	@echo "  make chunks"
	@echo "  make qc      RUN_DATE=YYYY-MM-DD"
	@echo "  make sample  N=10"

# Example query (adjust as needed)
TERM ?= "adverse drug reaction"[Title/Abstract] OR pharmacovigilance[Title/Abstract] OR "drug safety"[Title/Abstract]
RETMAX ?= 100
SLEEP ?= 8
RETRY ?= 3
BACKOFF ?= 20
RUN_DATE ?= YYYY-MM-DD
N ?= 10

fetch:
	python scripts/fetch_pmc_oai.py --term '$(TERM)' --retmax $(RETMAX) --sleep $(SLEEP) --retry $(RETRY) --backoff $(BACKOFF)

chunks:
	python scripts/extract_chunks_from_oai.py

qc:
	python scripts/qc_chunks.py --input artifacts/chunks.jsonl --report outputs/runs/$(RUN_DATE)/qc_chunks.json

sample:
	python scripts/sample_chunks.py --n $(N)
