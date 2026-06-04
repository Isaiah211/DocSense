import json
import pytest
from pathlib import Path
from starlette.testclient import TestClient


@pytest.fixture
def tmp_index(tmp_path, monkeypatch):
    data_index = tmp_path / "data" / "index"
    data_index.mkdir(parents=True)
    metadata = [
        {"file": "doc1.txt", "chunk_id": "c1", "text": "This is about budget forecast and finance."},
        {"file": "doc2.txt", "chunk_id": "c2", "text": "How to reset password on account."},
        {"file": "doc3.txt", "chunk_id": "c3", "text": "Admissions requirements for RPI."},
        {"file": "doc4.txt", "chunk_id": "c4", "text": "Supervised learning is a type of machine learning."},
        {"file": "doc5.txt", "chunk_id": "c5", "text": "Financial aid deadlines are important in 2025."},
        {"file": "doc6.txt", "chunk_id": "c6", "text": "Apple company overview and products."},
        {"file": "doc7.txt", "chunk_id": "c7", "text": "Apple is a fruit, sweet and crunchy."},
        {"file": "doc8.txt", "chunk_id": "c8", "text": "Install instructions for package manager."},
        {"file": "doc9.txt", "chunk_id": "c9", "text": "Payment methods include credit card and invoice."},
        {"file": "doc10.txt", "chunk_id": "c10", "text": "How to install Python packages using pip."},
        {"file": "doc11.txt", "chunk_id": "c11", "text": "Install guide for Ubuntu and system packages."},
    ]
    (data_index / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    # change cwd so app startup reads this metadata file
    monkeypatch.chdir(tmp_path)
    return metadata


@pytest.fixture
def client(tmp_index):
    # import here so that FastAPI startup reads tmp_index metadata
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def fake_sentence_transformers(monkeypatch):
    # Provide a lightweight fake SentenceTransformer to allow imports and a simple encode
    class _FakeModel:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, texts, show_progress_bar=False, convert_to_numpy=False):
            import numpy as np

            n = len(texts)
            return np.zeros((n, 8), dtype=float)

    fake_mod = type("mod", (), {"SentenceTransformer": _FakeModel})
    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", fake_mod)
    return _FakeModel
