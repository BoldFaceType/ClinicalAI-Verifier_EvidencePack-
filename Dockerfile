# ClinicalAI-Verifier â€” single-stage runtime image
#
# Build:
#   docker build -t clinica-ai-engineering .
#
# Run (validate-dsfe):
#   docker run --rm \
#     -v "$(pwd)/examples/preflight:/data/in:ro" \
#     -v "$(pwd)/out:/data/out" \
#     clinica-ai-engineering \
#     validate-dsfe /data/in/dsfe_input.csv /data/out
#
# Run (evidence-packer):
#   docker run --rm \
#     -v "$(pwd)/examples/evidence:/data/in:ro" \
#     -v "$(pwd)/out:/data/out" \
#     clinica-ai-engineering \
#     evidence-packer /data/in/claimresponse_denied.json /data/in/clinical_notes /data/out
#
# Custom rule config:
#   docker run --rm \
#     -v "$(pwd)/config.toml:/data/config.toml:ro" \
#     ... (same as above)
#   (config.toml is auto-detected from the /data working directory; no
#    extra flags needed. To use a different filename/path, set
#    -e CLINICAL_AI_CONFIG=/data/myconfig.toml instead.)

FROM python:3.11-slim

WORKDIR /app

# Install the package (with parquet extra) without dev/test files.
COPY pyproject.toml ./
COPY src ./src
COPY README.md ./

RUN pip install --no-cache-dir ".[parquet]"

# Default working directory for mounted input/output volumes.
RUN mkdir -p /data/in /data/out
WORKDIR /data

ENTRYPOINT []
CMD ["validate-dsfe", "--help"]