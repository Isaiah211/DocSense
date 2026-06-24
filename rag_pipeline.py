import argparse
import os
from typing import Optional

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
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
- If you cite evidence, mention the source document or chunk filename.
"""


DOCUMENT_PROMPT = PromptTemplate.from_template(
    "Source document: {source_document}\n"
    "Chunk file: {chunk_name}\n"
    "Query labels: {query_labels}\n"
    "Similarity score: {boosted_percentage:.2f}%\n"
    "Retrieved text:\n{page_content}"
)


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
        source_document = metadata.get("source_document", "unknown")
        chunk_name = metadata.get("chunk_name", "unknown")
        query_labels = metadata.get("query_labels", "None")
        similarity_score = metadata.get("similarity_score")
        boosted_percentage = metadata.get("boosted_percentage")

        similarity_text = f"{similarity_score:.4f}" if isinstance(similarity_score, (int, float)) else "unknown"
        boosted_text = f"{boosted_percentage:.2f}%" if isinstance(boosted_percentage, (int, float)) else "unknown"

        formatted_blocks.append(
            f"Context chunk {index}\n"
            f"Source document: {source_document}\n"
            f"Chunk file: {chunk_name}\n"
            f"Query labels: {query_labels}\n"
            f"Similarity score: {similarity_text}\n"
            f"Relevance percentage: {boosted_text}\n"
            f"Retrieved text:\n{document.page_content}"
        )

    return "\n\n---\n\n".join(formatted_blocks)


def build_rag_chain(model_name: str = "mistral", top_k: int = 3, base_url: Optional[str] = None):
    retriever = SemanticSearchRetriever(top_k=top_k)
    llm = ChatOllama(
        model=model_name,
        base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.0,
    )

    return (
        {
            "context": retriever | RunnableLambda(_format_documents),
            "input": RunnablePassthrough(),
        }
        | QA_PROMPT
        | llm
        | StrOutputParser()
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
            response = rag_chain.invoke(question)
            print("\nAnswer:\n")
            print(response)
            print("\n" + "=" * 72 + "\n")
        except Exception as exc:
            print("\nRAG request failed.")
            print("Make sure Ollama is running and the model is available locally.")
            print(f"Details: {exc}")
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()