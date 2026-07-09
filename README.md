# DocSense

A local, privacy-first document intelligence system powered by semantic search and retrieval-augmented generation (RAG). Ask natural-language questions about your personal documents and get grounded, citation-backed answers with full transparency.

**Status:** Active Development | **License:** MIT

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Usage](#usage)
  - [Web UI](#web-ui)
  - [REST API](#rest-api)
- [How It Works](#how-it-works)
- [Development](#development)
- [Contributing](#contributing)
- [FAQ](#faq)
- [Privacy & Security](#privacy--security)
- [Performance Tips](#performance-tips)
- [Authors](#authors)

## Overview

DocSense combines semantic search, retrieval-augmented generation (RAG), and multi-label classification to enable natural-language querying over personal document collections. All processing happens locally using local LLMs (Ollama) — your data never leaves your machine.

**Ideal for:** Bank statements, receipts, emails, notes, research papers, reports, and any collection of personal or business documents.

## Features

- **Semantic Search** — Find relevant documents using sentence embeddings, not keyword matching
- **Retrieval-Augmented Generation (RAG)** — Get answers grounded in your actual documents with automatic citations
- **Confidence & Citations** — Every answer includes similarity scores, source references, and relevance indicators
- **Multi-Label Classification** — Intelligent automatic tagging and document categorization
- **Local & Private** — Run entirely on your machine; no external API calls or cloud dependencies
- **Full-Stack UI** — Modern React dashboard (Vite) with dark mode and 3-panel layout
- **REST API** — FastAPI backend with Swagger documentation
- **Document Management** — Upload, remove, and manage your document corpus

## Installation

### Prerequisites

- Python 3.9 or higher
- Node.js 18+ (for frontend)
- Ollama installed locally ([download](https://ollama.ai))
- A local Ollama model running (e.g., `ollama pull mistral && ollama serve`)

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd DocSense
   ```

2. **Install backend dependencies**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install frontend dependencies**

   ```bash
   cd frontend
   pnpm install  # or npm install
   cd ..
   ```

## Quick Start

### 1. Prepare Your Documents

Place documents in the `data/` directory:

```bash
mkdir -p data/documents
# Add your .txt files here
```

### 2. Run the Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at `http://localhost:8000/docs`

### 3. Run the Frontend

In a separate terminal:

```bash
cd frontend
pnpm dev
```

UI available at `http://localhost:3000`

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Ollama Configuration
OLLAMA_MODEL=mistral
OLLAMA_BASE_URL=http://localhost:11434

# RAG Pipeline
RAG_SIMILARITY_THRESHOLD=0.45
RAG_TOP_K=3

# FastAPI
API_HOST=0.0.0.0
API_PORT=8000
```

### Semantic Search Tuning

Edit `semantic_search_utils.py` to customize:

- **Embedding model**: `BAAI/bge-small-en-v1.5` (configurable)
- **Device selection**: Automatically detects CUDA/MPS/CPU
- **Query expansion**: Custom term expansion logic
- **Label scoring**: Multi-label relevance scoring

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP API
┌──────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend                           │
│  ┌──────────────────┬──────────────────┬─────────────────┐  │
│  │  RAG Pipeline    │  Semantic Search │  Doc Management │  │
│  └──────────┬───────┴────────┬─────────┴────────┬────────┘  │
│             │                │                  │           │
│  ┌──────────▼──────┐  ┌──────▼────────┐  ┌──────▼──────┐    │
│  │  LangChain +    │  │  Sentence     │  │  Document   │    │
│  │  Ollama (Local  │  │  Transformers │  │  Chunking & │    │
│  │  LLMs)          │  │  (Embeddings) │  │  Indexing   │    │
│  └─────────────────┘  └───────────────┘  └─────────────┘    │
│                                                             │
│  Vector Index (embeddings.npy)                              │
│  Metadata Store (metadata.json)                             │
│  Labels Configuration (Labels.json)                         │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Web UI

1. Navigate to `http://localhost:3000`
2. Enter a query in the search box
3. Browse results with citations and confidence scores

Example queries:

- "Summarize my Q3 expenses across all reports"
- "Find receipts mentioning office supplies"
- "Which documents discuss machine learning?"
- "What did the January report say about budget?"

### REST API

**Query endpoint:**

```bash
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What were my total expenses last month?",
    "model": "mistral",
    "top_k": 3
  }'
```

**Response:**

```json
{
  "answer": "...",
  "citations": [...],
  "confidence": {...},
  "retrieval": [...]
}
```

**Key endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/rag/query` | Query documents with RAG |
| GET | `/api/documents` | List indexed documents |
| POST | `/api/documents/upload` | Upload new document |
| DELETE | `/api/documents/{doc_id}` | Remove document |
| GET | `/health` | Health check |

Full API documentation: `http://localhost:8000/docs`

## How It Works

### Semantic Search Pipeline

1. **Query Embedding** — User query is embedded using sentence transformers
2. **Vector Similarity** — Compared against document chunk embeddings
3. **Label Detection** — Query classified to relevant document categories
4. **Ranking** — Chunks scored by relevance and label match
5. **Retrieval** — Top-k results returned with metadata

### RAG (Retrieval-Augmented Generation)

1. **Retrieve** — Semantic search finds relevant chunks
2. **Augment** — Format chunks with citations and metadata
3. **Generate** — Pass to local LLM with strict constraints:
   - Answer only from provided context
   - Return "I don't know" if not found
   - No hallucination or external knowledge
4. **Return** — Answer with citations and confidence assessment

### Confidence Levels

- **High**: Multiple relevant sources, similarity > threshold
- **Medium**: Partial match, single source
- **Low**: Weak similarity or limited results (includes disclaimer)

## Development

### Project Structure

```
DocSense/
├── app/
│   ├── main.py              # FastAPI application
│   ├── ingest.py            # Document ingestion
│   └── __init__.py
├── frontend/                # React + Vite application
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   └── ingest.py            # Batch ingestion utility
├── chunks/                  # Pre-processed document chunks
├── data/                    # Raw documents and vector index
├── rag_pipeline.py          # RAG orchestration
├── rag_retriever.py         # Semantic search retriever
├── semantic_search_utils.py # Embedding and search utilities
├── requirements.txt
└── README.md
```

### Adding Features

**New RAG component:**

1. Extend `rag_retriever.py` for custom retrieval
2. Modify `rag_pipeline.py` to integrate
3. Add endpoint in `app/main.py`

**UI customization:**

1. Edit components in `frontend/src/`
2. Styling uses Tailwind CSS
3. Build: `pnpm build`

**Document type support:**

1. Implement parser in `Parse.py`
2. Update `app/ingest.py`
3. Test with `scripts/ingest.py`

### Running Tests

```bash
# Backend tests
pytest tests/

# Frontend tests
cd frontend && pnpm test
```

**Future improvement areas:**

- **Backend**: RAG improvements, retrieval strategies, performance optimization, new document ingestion from users
- **Frontend**: UI/UX enhancements, visualizations, accessibility
- **ML**: Better embeddings, fine-tuned classifiers, knowledge graphs
- **Documentation**: Examples, tutorials, guides

## FAQ

**Q: Can I use different LLMs?**  
A: Yes. Any Ollama-supported model works. Install with `ollama pull <model>` and specify in queries.

**Q: How do I handle large documents?**  
A: Use `Chunk.py` to split into semantic chunks before ingestion.

**Q: Is my data private?**  
A: Yes. All processing is local. No cloud calls, no external APIs.

**Q: How do I improve accuracy?**  
A: Fine-tune embeddings, improve chunking strategy, or add training examples to labels.

**Q: What document formats are supported?**  
A: Plain text (`.txt`) and CSV metadata. For the future, other formats can be added via `Parse.py`.

**Q: Can I export results?**  
A: Yes, the API returns structured JSON suitable for export and integration.

## Privacy & Security

- **Local Processing**: All computations happen on your machine
- **No Cloud Calls**: Documents never leave your system
- **No External APIs**: Vector embeddings generated locally
- **Ideal for**: Financial records, medical documents, legal files, and other sensitive data

## Performance Tips

- Use GPU when available (auto-detected: CUDA, MPS, or CPU)
- Batch process large document collections with `scripts/ingest.py`
- Adjust `top_k` parameter: lower for speed, higher for coverage
- Select appropriate embedding model: `bge-small` for speed, larger for accuracy

## Authors

- **Isaiah Mathew** — RAG pipeline, ML, LLM integration, Frontend & integration
- **Anthony Mirabal** — Semantic Search, Classifier, Parser/Chunker, Data collection

---

