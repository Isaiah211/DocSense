import json
import os
from functools import lru_cache
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util


PROCESSED_DIR = "chunks"
CONFIG_FILE = "Labels.json"
METADATA_FILE = os.path.join(PROCESSED_DIR, "metadata.json")
EMBEDDINGS_FILE = os.path.join(PROCESSED_DIR, "embeddings.npy")
EMBEDDER_NAME = "BAAI/bge-small-en-v1.5"


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Any]:
    with open(CONFIG_FILE, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


@lru_cache(maxsize=1)
def load_metadata() -> Dict[str, Dict[str, Any]]:
    with open(METADATA_FILE, "r", encoding="utf-8") as metadata_file:
        return json.load(metadata_file)


@lru_cache(maxsize=1)
def load_doc_embeddings() -> np.ndarray:
    return np.load(EMBEDDINGS_FILE)


@lru_cache(maxsize=1)
def load_chunk_documents() -> Tuple[List[str], List[str]]:
    metadata = load_metadata()
    chunks_text: List[str] = []
    chunks_filenames: List[str] = []

    for chunk_file in metadata.keys():
        chunk_path = os.path.join(PROCESSED_DIR, chunk_file)
        with open(chunk_path, "r", encoding="utf-8") as chunk_handle:
            chunks_text.append(chunk_handle.read())
        chunks_filenames.append(chunk_file)

    return chunks_text, chunks_filenames


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDER_NAME, device=get_device())


def _expand_query(query: str) -> str:
    normalized_query = query.lower().strip()
    query_words = normalized_query.replace("?", "").replace("'", " ").split()

    expansion_terms = ""
    has_ai_intent = any(word in query_words for word in ["ai", "ais", "bot", "bots", "app", "apps", "software"])
    has_weather_intent = any(word in query_words for word in ["weather", "forecast", "forecasts", "climate", "seasons"])

    if has_ai_intent and has_weather_intent:
        expansion_terms = " personalized weather messenger slack bot integration consumer app client update"
    elif has_ai_intent:
        expansion_terms = " software chatbot app integration service automated tool utility engineering implementation"

    return normalized_query + expansion_terms


def _score_query_categories(query_embedding: torch.Tensor, categories: List[Dict[str, Any]], embedder: SentenceTransformer) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    category_scores: Dict[str, float] = {}

    for category in categories:
        category_id = category.get("id", "Unknown")
        phrases = category.get("search_phrases", [])
        if not phrases:
            category_scores[category_id] = 0.0
            continue

        phrase_embeddings = embedder.encode(phrases, convert_to_tensor=True, device=query_embedding.device)
        phrase_scores = util.cos_sim(query_embedding, phrase_embeddings)[0]
        category_scores[category_id] = float(torch.max(phrase_scores).item())

    if not category_scores:
        return category_scores, []

    max_score = max(category_scores.values())
    dynamic_threshold = max(0.10, max_score - 0.12)
    detected_labels = [
        {"id": category_id, "score": score_value}
        for category_id, score_value in category_scores.items()
        if score_value >= dynamic_threshold
    ]
    detected_labels.sort(key=lambda item: item["score"], reverse=True)
    return category_scores, detected_labels


def search_chunks(query: str, top_k: int = 3) -> Dict[str, Any]:
    if not all(os.path.exists(path) for path in [METADATA_FILE, EMBEDDINGS_FILE, CONFIG_FILE]):
        raise FileNotFoundError("Missing database files or Labels.json template configuration.")

    config_data = load_config()
    categories = config_data.get("candidate_labels", [])
    metadata = load_metadata()
    doc_embeddings = load_doc_embeddings()
    chunks_text, chunks_filenames = load_chunk_documents()

    device = get_device()
    embedder = get_embedder()
    expanded_query = _expand_query(query)
    query_embedding = embedder.encode(expanded_query, convert_to_tensor=True, device=device)

    category_scores, detected_labels = _score_query_categories(query_embedding, categories, embedder)

    doc_embeddings_tensor = torch.from_numpy(doc_embeddings).to(device)
    similarity_scores = util.cos_sim(query_embedding, doc_embeddings_tensor)[0]

    top_k = min(top_k, len(chunks_text))
    top_indices = similarity_scores.argsort(descending=True)[:top_k]

    results: List[Dict[str, Any]] = []
    for rank, index_tensor in enumerate(top_indices, 1):
        idx = int(index_tensor.item())
        raw_score = float(similarity_scores[idx].item())

        floor = 0.42
        ceiling = 0.82
        normalized_score = (raw_score - floor) / (ceiling - floor)
        boosted_percentage = min(100.0, max(0.0, normalized_score * 100))
        if raw_score > 0.55 and boosted_percentage < 50.0:
            boosted_percentage = 65.0 + (raw_score * 10)

        chunk_name = chunks_filenames[idx]
        chunk_metadata = dict(metadata.get(chunk_name, {}))
        chunk_path = os.path.join(PROCESSED_DIR, chunk_name)
        chunk_text = chunks_text[idx]

        results.append(
            {
                "rank": rank,
                "chunk_name": chunk_name,
                "chunk_path": chunk_path,
                "text": chunk_text,
                "metadata": chunk_metadata,
                "similarity_score": raw_score,
                "boosted_percentage": boosted_percentage,
            }
        )

    return {
        "query": query,
        "expanded_query": expanded_query,
        "detected_labels": detected_labels,
        "category_scores": category_scores,
        "results": results,
        "device": device,
    }


def get_search_assets_exist() -> bool:
    return all(os.path.exists(path) for path in [METADATA_FILE, EMBEDDINGS_FILE, CONFIG_FILE])