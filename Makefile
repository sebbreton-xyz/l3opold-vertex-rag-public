.PHONY: help fetch chunks qc sample

help:
	@echo "Targets:"
	@echo "  make fetch   TERM='...' RETMAX=100 SLEEP=8 RETRY=3 BACKOFF=20"
	@echo "  make chunks"
	@echo "  make qc      RUN_DATE=YYYY-MM-DD"
	@echo "  make sample  N=10"

# Example query (adjust as needed)
PMC_TERM ?= (("adverse drug reaction"[Title/Abstract] OR pharmacovigilance[Title/Abstract] OR "drug safety"[Title/Abstract]) AND pmc-open[sb])

# Tunables
RETMAX ?= 100
OUT_DIR ?= data/raw/pmc_xml
SLEEP ?= 8
RETRY ?= 3
BACKOFF ?= 20

RUN_DATE ?= YYYY-MM-DD
N ?= 10

fetch:
	python scripts/fetch_pmc_oai.py --term '$(PMC_TERM)' --retmax $(RETMAX) --out-dir $(OUT_DIR) --sleep $(SLEEP) --retry $(RETRY) --backoff $(BACKOFF)

chunks:
	python scripts/extract_chunks_from_oai.py

qc:
	python scripts/qc_chunks.py --input artifacts/chunks.jsonl --report outputs/runs/$(RUN_DATE)/qc_chunks.json

sample:
	python scripts/sample_chunks.py --n $(N)