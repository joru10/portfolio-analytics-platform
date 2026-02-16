import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings


def _prepare_prompt(question: str, context_type: str, context: dict[str, Any]) -> tuple[str, str]:
    context_json = json.dumps(context, ensure_ascii=True, separators=(",", ":"))
    if len(context_json) > 16000:
        context_json = context_json[:16000] + "...<truncated>"

    system_prompt = (
        "You are a portfolio analytics assistant. "
        "Use only the provided context data. "
        "Return concise, practical insights with explicit numbers where available. "
        "Include: (1) key findings, (2) risks, (3) concrete next checks. "
        "If data is insufficient, state what is missing."
    )
    user_prompt = (
        f"Context type: {context_type}\n"
        f"Question: {question}\n"
        f"Context JSON: {context_json}"
    )
    return system_prompt, user_prompt


def _call_openai(model: str, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured on backend")

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
        "max_output_tokens": max_tokens,
    }

    req = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=35) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        raise RuntimeError(f"OpenAI request failed: {detail[:300]}") from exc
    except URLError as exc:
        raise RuntimeError(f"OpenAI request failed: {exc}") from exc

    output = data.get("output", [])
    texts: list[str] = []
    for item in output:
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                texts.append(text)

    answer = "\n".join(texts).strip() or data.get("output_text", "").strip()
    if not answer:
        raise RuntimeError("OpenAI returned empty response")
    return answer


def _call_anthropic(model: str, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured on backend")

    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    req = Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=35) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        raise RuntimeError(f"Anthropic request failed: {detail[:300]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Anthropic request failed: {exc}") from exc

    content = data.get("content", [])
    texts = [c.get("text", "") for c in content if c.get("type") == "text" and c.get("text")]
    answer = "\n".join(texts).strip()
    if not answer:
        raise RuntimeError("Anthropic returned empty response")
    return answer


def generate_ai_explanation(
    question: str,
    context_type: str,
    context: dict[str, Any],
    provider: str | None,
    model: str | None,
    max_tokens: int,
) -> tuple[str, str, str]:
    chosen_provider = (provider or settings.ai_default_provider).strip().lower()
    system_prompt, user_prompt = _prepare_prompt(question=question, context_type=context_type, context=context)

    if chosen_provider == "openai":
        chosen_model = model or settings.openai_model
        answer = _call_openai(chosen_model, system_prompt, user_prompt, max_tokens)
        return chosen_provider, chosen_model, answer

    if chosen_provider == "anthropic":
        chosen_model = model or settings.anthropic_model
        answer = _call_anthropic(chosen_model, system_prompt, user_prompt, max_tokens)
        return chosen_provider, chosen_model, answer

    raise ValueError("Unsupported AI provider. Use 'openai' or 'anthropic'.")
