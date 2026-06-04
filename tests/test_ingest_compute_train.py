import sys
from pathlib import Path


def test_chunk_text_short():
    from scripts.ingest import chunk_text

    s = "Short text"
    chunks = chunk_text(s, chunk_size=100, overlap=10)
    assert isinstance(chunks, list)
    assert len(chunks) == 1
    assert chunks[0] == s


def test_compute_embeddings_missing_meta(monkeypatch, tmp_path, fake_sentence_transformers):
    # ensure compute_embeddings raises when metadata missing
    from scripts.compute_embeddings import main

    # run with argv pointing to a non-existent meta file
    monkeypatch.setattr(sys, "argv", ["compute_embeddings.py", "--meta", str(tmp_path / "no_meta.json")])
    try:
        main()
    except FileNotFoundError:
        assert True
    else:
        raise AssertionError("Expected FileNotFoundError for missing metadata")


def test_train_classifier_missing_embeddings(monkeypatch, tmp_path):
    from scripts import train_classifier

    monkeypatch.setattr(sys, "argv", ["train_classifier.py", "--emb", str(tmp_path / "no.npy")])
    try:
        train_classifier.main()
    except FileNotFoundError:
        assert True
    else:
        raise AssertionError("Expected FileNotFoundError when embeddings missing")
