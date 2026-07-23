"""
Couche d'accès aux API : chaque fonction prend un prompt et retourne
un dict standardisé {provider, model, raw_response, error, latency_ms}.
"""
from __future__ import annotations

import time
from typing import Any

from config import PROVIDERS, REQUEST_TIMEOUT


def _safe_call(provider_key: str, callable_fn) -> dict[str, Any]:
    """Enrobe un appel API dans la gestion d'erreur + mesure de latence."""
    cfg = PROVIDERS[provider_key]
    start = time.perf_counter()
    try:
        text = callable_fn()
        latency = (time.perf_counter() - start) * 1000
        return {
            "provider": cfg.name,
            "model": cfg.model,
            "raw_response": text,
            "error": None,
            "latency_ms": round(latency, 1),
        }
    except Exception as exc:
        latency = (time.perf_counter() - start) * 1000
        return {
            "provider": cfg.name,
            "model": cfg.model,
            "raw_response": None,
            "error": f"{type(exc).__name__}: {exc}",
            "latency_ms": round(latency, 1),
        }


# ---------------------------------------------------------------------------
# OpenAI (ChatGPT)
# ---------------------------------------------------------------------------
def query_openai(prompt: str) -> dict[str, Any]:
    import openai

    def _call() -> str:
        client = openai.OpenAI(api_key=PROVIDERS["openai"].api_key)
        response = client.chat.completions.create(
            model=PROVIDERS["openai"].model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=REQUEST_TIMEOUT,
        )
        return response.choices[0].message.content.strip()

    return _safe_call("openai", _call)


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------
def query_anthropic(prompt: str) -> dict[str, Any]:
    import anthropic

    def _call() -> str:
        client = anthropic.Anthropic(api_key=PROVIDERS["anthropic"].api_key)
        response = client.messages.create(
            model=PROVIDERS["anthropic"].model,
            max_tokens=2048,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )
        # Anthropic renvoie un bloc de type 'text'
        block = response.content[0]
        if hasattr(block, "text"):
            return block.text.strip()
        return str(block).strip()

    return _safe_call("anthropic", _call)


# ---------------------------------------------------------------------------
# Mistral AI
# ---------------------------------------------------------------------------
def query_mistral(prompt: str) -> dict[str, Any]:
    from mistralai import Mistral

    def _call() -> str:
        client = Mistral(api_key=PROVIDERS["mistral"].api_key)
        response = client.chat.complete(
            model=PROVIDERS["mistral"].model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout_ms=REQUEST_TIMEOUT * 1000,
        )
        return response.choices[0].message.content.strip()

    return _safe_call("mistral", _call)


# ---------------------------------------------------------------------------
# DeepSeek (API compatible OpenAI)
# ---------------------------------------------------------------------------
def query_deepseek(prompt: str) -> dict[str, Any]:
    import openai

    def _call() -> str:
        client = openai.OpenAI(
            api_key=PROVIDERS["deepseek"].api_key,
            base_url="https://api.deepseek.com",
        )
        response = client.chat.completions.create(
            model=PROVIDERS["deepseek"].model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=REQUEST_TIMEOUT,
        )
        return response.choices[0].message.content.strip()

    return _safe_call("deepseek", _call)


# ---------------------------------------------------------------------------
# Gemini (Google)
# ---------------------------------------------------------------------------
def query_gemini(prompt: str) -> dict[str, Any]:
    import google.generativeai as genai

    def _call() -> str:
        genai.configure(api_key=PROVIDERS["gemini"].api_key)
        model = genai.GenerativeModel(PROVIDERS["gemini"].model)
        response = model.generate_content(prompt)
        return response.text.strip()

    return _safe_call("gemini", _call)


# ---------------------------------------------------------------------------
# AI21 (Jamba)
# ---------------------------------------------------------------------------
def query_ai21(prompt: str) -> dict[str, Any]:
    import openai

    def _call() -> str:
        client = openai.OpenAI(
            api_key=PROVIDERS["ai21"].api_key,
            base_url="https://api.ai21.com/studio/v1",
        )
        response = client.chat.completions.create(
            model=PROVIDERS["ai21"].model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=REQUEST_TIMEOUT,
        )
        return response.choices[0].message.content.strip()

    return _safe_call("ai21", _call)


# ---------------------------------------------------------------------------
# Dispatcheur
# ---------------------------------------------------------------------------
QUERY_FUNCTIONS = {
    "openai": query_openai,
    "anthropic": query_anthropic,
    "mistral": query_mistral,
    "deepseek": query_deepseek,
    "gemini": query_gemini,
    "ai21": query_ai21,
}


def query_all(prompt: str, providers: list[str] | None = None) -> list[dict[str, Any]]:
    """Interroge tous les fournisseurs (ou une sélection)."""
    if providers is None:
        providers = list(QUERY_FUNCTIONS)
    results = []
    for key in providers:
        if not PROVIDERS[key].api_key:
            results.append({
                "provider": PROVIDERS[key].name,
                "model": PROVIDERS[key].model,
                "raw_response": None,
                "error": "Missing API key – set in .env",
                "latency_ms": 0,
            })
            continue
        results.append(QUERY_FUNCTIONS[key](prompt))
    return results
