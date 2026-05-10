"""Groq chat completions for grounded RAG answers."""

import os

from groq import APIStatusError, Groq, RateLimitError


def get_llm_response(prompt: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY must be set in .env")

    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        msg = response.choices[0].message.content
        return (msg or "").strip()
    except RateLimitError as e:
        raise RuntimeError("LLM_MODEL_OVERLOADED") from e
    except APIStatusError as e:
        if e.status_code in (429, 503):
            raise RuntimeError("LLM_MODEL_OVERLOADED") from e
        raise RuntimeError("Failed to generate content from Groq") from e
