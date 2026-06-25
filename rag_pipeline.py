import argparse
import os
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_ollama import ChatOllama

from rag_retriever import SemanticSearchRetriever


STRICT_RAG_SYSTEM_PROMPT = """You are a careful document question-answering assistant.

Use only the supplied context to answer the user's question.
The context contains retrieved chunks plus metadata such as source document names,
chunk filenames, similarity scores, and classification labels.

Rules:
- Answer only from the provided context.
- If the context does not contain the answer, reply exactly: I don't know.
- Do not invent facts, do not use outside knowledge, and do not guess.
- Prefer concise answers with direct support from the retrieved evidence.
- If you cite evidence, mention the citation IDs shown in the context.
"""


LOW_CONFIDENCE_DISCLAIMER = "\n Note: retrieval similarity was low, so this answer may be incomplete."

SIMILARITY_THRESHOLD = 0.45
SIMILARITY_MARGIN_THRESHOLD = 0.05


QA_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", STRICT_RAG_SYSTEM_PROMPT),
        (
            "human",
            "Retrieved context:\n{context}\n\n"
            "Question: {input}\n\n"
            "Use only the retrieved context to answer. If the answer is not present, say I don't know.",
        ),
    ]
)


def _format_documents(documents: list[Document]) -> str:
    if not documents:
        return "No relevant context was retrieved."

    formatted_blocks = []
    for index, document in enumerate(documents, 1):
        metadata = document.metadata or {}
        citation_id = metadata.get("citation_id", f"[{index}]")
        source_document = metadata.get("source_document", "unknown")
        chunk_name = metadata.get("chunk_name", "unknown")
        query_labels = metadata.get("query_labels", "None")
        similarity_score = metadata.get("similarity_score")
        boosted_percentage = metadata.get("boosted_percentage")

        similarity_text = f"{similarity_score:.4f}" if isinstance(similarity_score, (int, float)) else "unknown"
        boosted_text = f"{boosted_percentage:.2f}%" if isinstance(boosted_percentage, (int, float)) else "unknown"

        formatted_blocks.append(
            f"Citation {citation_id}\n"
            f"Source document: {source_document}\n"
            f"Chunk file: {chunk_name}\n"
            f"Query labels: {query_labels}\n"
            f"Similarity score: {similarity_text}\n"
            f"Relevance percentage: {boosted_text}\n"
            f"Retrieved text:\n{document.page_content}"
        )

    return "\n\n---\n\n".join(formatted_blocks)


def _determine_confidence(documents: List[Document]) -> Dict[str, Any]:
    if not documents:
        return {
            "level": "low",
            "top_similarity": 0.0,
            "similarity_margin": 0.0,
            "is_low_confidence": True,
        }

    similarities = [float((doc.metadata or {}).get("similarity_score", 0.0) or 0.0) for doc in documents]
    top_similarity = similarities[0] if similarities else 0.0
    second_similarity = similarities[1] if len(similarities) > 1 else 0.0
    similarity_margin = top_similarity - second_similarity

    if top_similarity < SIMILARITY_THRESHOLD:
        level = "low"
    elif top_similarity < SIMILARITY_THRESHOLD + 0.12:
        # Borderline top similarity: require a good margin to be medium, otherwise low
        if similarity_margin < SIMILARITY_MARGIN_THRESHOLD:
            level = "low"
        else:
            level = "medium"
    else:
        # High similarity: if similarity margin is small, it's fine, we still have a very strong top match.
        level = "high"

    return {
        "level": level,
        "top_similarity": top_similarity,
        "similarity_margin": similarity_margin,
        "is_low_confidence": level == "low",
    }


def _build_citations(documents: List[Document]) -> List[Dict[str, Any]]:
    citations: List[Dict[str, Any]] = []
    for index, document in enumerate(documents, 1):
        metadata = document.metadata or {}
        citations.append(
            {
                "citation_id": metadata.get("citation_id", f"[{index}]"),
                "source_document": metadata.get("source_document", "unknown"),
                "chunk_name": metadata.get("chunk_name", "unknown"),
                "chunk_path": metadata.get("chunk_path", ""),
                "similarity_score": metadata.get("similarity_score", 0.0),
                "boosted_percentage": metadata.get("boosted_percentage", 0.0),
                "query_labels": metadata.get("query_labels", "None"),
            }
        )
    return citations


def _build_response_payload(question: str, documents: List[Document], answer_text: str) -> Dict[str, Any]:
    confidence = _determine_confidence(documents)
    citations = _build_citations(documents)
    retrieval = [
        {
            "citation_id": (doc.metadata or {}).get("citation_id", f"[{index}]"),
            "source_document": (doc.metadata or {}).get("source_document", "unknown"),
            "chunk_name": (doc.metadata or {}).get("chunk_name", "unknown"),
            "chunk_path": (doc.metadata or {}).get("chunk_path", ""),
            "similarity_score": (doc.metadata or {}).get("similarity_score", 0.0),
            "boosted_percentage": (doc.metadata or {}).get("boosted_percentage", 0.0),
            "query_labels": (doc.metadata or {}).get("query_labels", "None"),
            "text": doc.page_content,
        }
        for index, doc in enumerate(documents, 1)
    ]

    return {
        "query": question,
        "answer": _append_low_confidence_disclaimer(answer_text, confidence["is_low_confidence"]),
        "citations": citations,
        "confidence": {
            **confidence,
            "thresholds": {
                "top_similarity": SIMILARITY_THRESHOLD,
                "similarity_margin": SIMILARITY_MARGIN_THRESHOLD,
            },
        },
        "fallback": LOW_CONFIDENCE_DISCLAIMER if confidence["is_low_confidence"] else "",
        "retrieval": retrieval,
    }


def _append_low_confidence_disclaimer(answer_text: str, is_low_confidence: bool) -> str:
    normalized_answer = answer_text.strip() if answer_text else ""
    if not is_low_confidence:
        return normalized_answer

    if not normalized_answer:
        normalized_answer = "I don't know."

    if LOW_CONFIDENCE_DISCLAIMER.lower() in normalized_answer.lower():
        return normalized_answer

    separator = " " if normalized_answer.endswith(('.', '!', '?')) else "."
    return f"{normalized_answer}{separator} {LOW_CONFIDENCE_DISCLAIMER}"


def build_rag_chain(model_name: str = "mistral", top_k: int = 3, base_url: Optional[str] = None):
    retriever = SemanticSearchRetriever(top_k=top_k)
    llm = ChatOllama(
        model=model_name,
        base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.0,
    )

    answer_chain = (
        {
            "context": RunnableLambda(lambda payload: _format_documents(payload["documents"])),
            "input": RunnableLambda(lambda payload: payload["input"]),
        }
        | QA_PROMPT
        | llm
        | StrOutputParser()
    )

    response_builder = RunnableLambda(
        lambda payload: _build_response_payload(payload["input"], payload["documents"], payload["answer"])
    )

    return (
        RunnablePassthrough.assign(documents=RunnableLambda(lambda payload: retriever.invoke(payload["input"])))
        .assign(answer=answer_chain)
        | response_builder
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DocSense as a local RAG pipeline with Ollama.")
    parser.add_argument("--model", default=os.getenv("DOCSENSE_OLLAMA_MODEL", "mistral"), help="Ollama model name")
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieved chunks to pass to the LLM")
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama server base URL",
    )
    args = parser.parse_args()

    rag_chain = build_rag_chain(model_name=args.model, top_k=args.top_k, base_url=args.base_url)

    print(f"--- DocSense RAG ready using Ollama model '{args.model}' ---")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("Ask a question: ").strip()
        if not question or question.lower() == "exit":
            break

        try:
            response = rag_chain.invoke({"input": question})
            print("\nAnswer:\n")
            print(response["answer"])
            if response.get("citations"):
                print("\nCitations:")
                for citation in response["citations"]:
                    print(
                        f"{citation['citation_id']} {citation['source_document']} | {citation['chunk_name']} | "
                        f"score={citation['similarity_score']:.4f}"
                    )
            print("\n" + "=" * 72 + "\n")
        except Exception as exc:
            print("\nRAG request failed.")
            print("Make sure Ollama is running and the model is available locally.")
            print(f"Details: {exc}")
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()