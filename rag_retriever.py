from typing import Any, List

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

from semantic_search_utils import search_chunks


class SemanticSearchRetriever(BaseRetriever):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    top_k: int = 3

    def _get_relevant_documents(self, query: str, *, run_manager: Any = None) -> List[Document]:
        search_response = search_chunks(query=query, top_k=self.top_k)
        detected_labels = search_response.get("detected_labels", [])
        label_summary = ", ".join([f"{item['id']} ({item['score'] * 100:.1f}%)" for item in detected_labels]) if detected_labels else "None"

        documents: List[Document] = []
        for result in search_response.get("results", []):
            metadata = dict(result.get("metadata", {}))
            metadata.update(
                {
                    "rank": result.get("rank"),
                    "citation_id": f"[{result.get('rank')}]",
                    "chunk_name": result.get("chunk_name"),
                    "chunk_path": result.get("chunk_path"),
                    "similarity_score": result.get("similarity_score"),
                    "boosted_percentage": result.get("boosted_percentage"),
                    "query_labels": label_summary,
                }
            )
            documents.append(Document(page_content=result.get("text", ""), metadata=metadata))

        return documents
