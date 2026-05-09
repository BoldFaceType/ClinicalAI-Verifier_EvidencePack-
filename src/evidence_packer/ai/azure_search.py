from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evidence_packer.models.fhir_models import ClinicalNote


@dataclass(frozen=True)
class SearchResult:
    source: str
    text: str
    score: float


class AzureAISearchRetriever:
    def __init__(self, *, endpoint: str, index_name: str, credential: Any) -> None:
        try:
            from azure.search.documents import SearchClient
        except ImportError as exc:
            raise RuntimeError(
                "Azure AI Search support requires installing the azure extra: "
                "pip install -e .[azure]"
            ) from exc

        self._client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential,
        )

    def search(self, query: str, *, top: int = 5) -> list[SearchResult]:
        results: list[SearchResult] = []
        for item in self._client.search(search_text=query, top=top):
            source = str(item.get("source", ""))
            text = str(item.get("text", ""))
            score = float(item.get("@search.score", 0.0) or 0.0)
            if source and text:
                results.append(SearchResult(source=source, text=text, score=score))
        return results


def to_clinical_notes(results: list[SearchResult]) -> list[ClinicalNote]:
    return [ClinicalNote(source=item.source, text=item.text) for item in results]

