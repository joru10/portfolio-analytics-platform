from app.api import ai as ai_api


def test_ai_explain_success(client, monkeypatch) -> None:
    def fake_generate(**kwargs):
        return "openai", "gpt-5-mini", "Key findings: ..."

    monkeypatch.setattr(ai_api, "generate_ai_explanation", fake_generate)

    response = client.post(
        "/v1/ai/explain",
        json={
            "question": "What are the key risks?",
            "context_type": "compare",
            "context": {"summary": [{"symbol": "AAPL", "return_pct": 0.1}]},
            "provider": "openai",
            "model": "gpt-5-mini",
            "max_tokens": 500,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "openai"
    assert payload["model"] == "gpt-5-mini"
    assert "Key findings" in payload["answer"]


def test_ai_explain_bad_provider_returns_400(client, monkeypatch) -> None:
    def fake_generate(**kwargs):
        raise ValueError("Unsupported AI provider")

    monkeypatch.setattr(ai_api, "generate_ai_explanation", fake_generate)

    response = client.post(
        "/v1/ai/explain",
        json={"question": "Explain", "context_type": "compare", "context": {}},
    )

    assert response.status_code == 400


def test_ai_explain_upstream_failure_returns_502(client, monkeypatch) -> None:
    def fake_generate(**kwargs):
        raise RuntimeError("OpenAI request failed")

    monkeypatch.setattr(ai_api, "generate_ai_explanation", fake_generate)

    response = client.post(
        "/v1/ai/explain",
        json={"question": "Explain", "context_type": "compare", "context": {}},
    )

    assert response.status_code == 502
