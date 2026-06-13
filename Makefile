# ClinicalAI-Verifier â€” dev/deploy convenience targets
#
# Usage: make <target>
#   make install   Install package + dev deps (editable)
#   make lint      Run ruff
#   make test      Run unit tests
#   make validate  Run validate-dsfe against the sample input
#   make pack      Run evidence-packer against the sample claim/notes
#   make clean     Remove caches, build artifacts, and sample run output

.PHONY: install lint test validate pack clean

PYTHON ?= python3
SAMPLE_DSFE := examples/preflight/dsfe_input.csv
SAMPLE_CLAIM := examples/evidence/claimresponse_denied.json
SAMPLE_NOTES := examples/evidence/clinical_notes
OUT_DIR := out

install:
	$(PYTHON) -m pip install -e ".[parquet]" --group dev

lint:
	ruff check src tests

test:
	$(PYTHON) -m unittest discover -s tests -v

validate:
	validate-dsfe $(SAMPLE_DSFE) $(OUT_DIR)/validate

pack:
	evidence-packer $(SAMPLE_CLAIM) $(SAMPLE_NOTES) $(OUT_DIR)/pack

clean:
	rm -rf $(OUT_DIR) .test_runs .tmp
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
	find . -type d -name '*.egg-info' -not -path './.venv/*' -exec rm -rf {} +