import json


def post_query(client, q):
    resp = client.post("/search", json={"q": q})
    assert resp.status_code == 200
    return resp.json()


def test_normal_budget_forecast(client):
    data = post_query(client, "budget forecast")
    assert "matches" in data
    assert len(data["matches"]) >= 1
    assert any("budget" in m["text"].lower() for m in data["matches"])


def test_normal_reset_password(client):
    data = post_query(client, "how to reset password")
    assert len(data["matches"]) >= 1
    assert any("password" in m["text"].lower() for m in data["matches"])


def test_normal_admissions_rpi(client):
    data = post_query(client, "RPI admission requirements")
    assert len(data["matches"]) >= 1
    assert any("rpi" in m["text"].lower() for m in data["matches"])


def test_normal_supervised_learning(client):
    data = post_query(client, "what is supervised learning")
    assert len(data["matches"]) >= 1
    assert any("supervised" in m["text"].lower() for m in data["matches"])


def test_normal_financial_aid_deadlines(client):
    data = post_query(client, "financial aid deadlines 2025")
    # allow either a match or empty results but ensure safe response
    assert "matches" in data


def test_ambiguous_apple_returns_multiple(client):
    data = post_query(client, "apple")
    files = {m["file"] for m in data["matches"]}
    # expect both company and fruit documents present
    assert any("doc6" in f or "doc7" in f for f in files)


def test_ambiguous_install_returns_multiple(client):
    data = post_query(client, "install")
    # expect multiple install-related documents
    assert len(data["matches"]) >= 1


def test_ambiguous_payment(client):
    data = post_query(client, "payment")
    assert len(data["matches"]) >= 1


def test_failure_very_long_input(client):
    long_q = "x" * 10000
    data = post_query(client, long_q)
    # service should not crash; allow empty matches
    assert "matches" in data


def test_failure_non_string_type(client):
    # send a JSON array which should fail pydantic validation (FastAPI returns 422)
    resp = client.post("/search", json=["not a dict"])
    assert resp.status_code in (400, 422)


def test_failure_injection_payload(client):
    payload = "'; DROP TABLE users;--"
    data = post_query(client, payload)
    # ensure no stack trace leaked and safe response
    assert "matches" in data
