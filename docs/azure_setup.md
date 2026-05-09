# Azure AI Setup

The standard package has no mandatory cloud dependency.

Install the optional Azure path when you want to connect the demo to Azure AI Search and Azure OpenAI:

```bash
pip install -e ".[azure]"
```

## Azure OpenAI

Set these environment variables:

```bash
AZURE_OPENAI_ENDPOINT=https://<resource-name>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>
AZURE_OPENAI_API_VERSION=2024-10-21
```

Then run:

```bash
evidence-packer examples/evidence_ai/claimresponse_denied.json examples/evidence_ai/clinical_notes out/evidence_ai --mode ai-assisted --verify-citations
```

## Azure AI Search

`evidence_packer.ai.azure_search.AzureAISearchRetriever` provides a small adapter for retrieving indexed clinical note chunks. Keep retrieved documents shaped with at least:

```json
{
  "source": "note_id_or_file_name",
  "text": "note chunk text"
}
```

The verifier still requires AI-proposed quotes to appear verbatim in the retrieved note text.

