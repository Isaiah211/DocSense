import csv
import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "example_inputs.csv"


def load_example_rows():
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture
def example_index(tmp_path, monkeypatch):
    rows = load_example_rows()
    metadata = []

    for row in rows:
        doc_path = ROOT / row["doc_path"]
        metadata.append(
            {
                "file": row["doc_path"],
                "chunk_id": f"{doc_path.name}::chunk::0",
                "text": doc_path.read_text(encoding="utf-8"),
            }
        )

    data_index = tmp_path / "data" / "index"
    data_index.mkdir(parents=True)
    (data_index / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return rows


@pytest.fixture
def client(example_index):
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_example_manifest_counts(example_index):
    counts = {"normal": 0, "ambiguous": 0, "adversarial": 0}
    for row in example_index:
        counts[row["case_type"]] += 1

    assert counts == {"normal": 5, "ambiguous": 3, "adversarial": 3}


def test_example_inputs_through_current_search(client, example_index):
    for row in example_index:
        resp = client.post("/search", json={"q": row["probe_query"]})
        assert resp.status_code == 200

        data = resp.json()
        assert "matches" in data

        min_matches = int(row["expected_min_matches"])
        max_matches = int(row["expected_max_matches"])
        assert min_matches <= len(data["matches"]) <= max_matches

        if row["case_type"] == "normal":
            assert len(data["matches"]) == 1
            assert data["matches"][0]["file"] == row["doc_path"]

        if row["case_type"] == "ambiguous":
            assert len(data["matches"]) >= 2

        if row["case_type"] == "adversarial":
            assert len(data["matches"]) == 0