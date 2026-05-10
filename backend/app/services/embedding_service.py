"""NVIDIA embedding API."""

import json
import os
from typing import Literal

import httpx
from dotenv import load_dotenv

load_dotenv()

InputType = Literal["passage", "query"]


def get_embedding(
    text: str | list[str],
    input_type: InputType = "passage",
):
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    nvidia_url = os.getenv("NVIDIA_API_URL")

    if not nvidia_key:
        raise RuntimeError("NVIDIA_API_KEY missing in .env")

    if not nvidia_url:
        raise RuntimeError("NVIDIA_API_URL missing in .env")

    texts = text if isinstance(text, list) else [text]

    headers = {
        "Authorization": f"Bearer {nvidia_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "input": texts,
        "model": "nvidia/nv-embedqa-e5-v5",
        "encoding_format": "float",
        "input_type": input_type,
    }

    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                nvidia_url,
                headers=headers,
                json=payload,
            )


        response.raise_for_status()

        result = response.json()

        embeddings = [
            item["embedding"]
            for item in result["data"]
        ]

        return embeddings if isinstance(text, list) else embeddings[0]

    except httpx.HTTPStatusError:
        try:
            err = response.json()
            detail = err.get("detail", response.text)
        except json.JSONDecodeError:
            detail = response.text

        raise RuntimeError(f"NVIDIA API Error: {detail}")

    except Exception as e:
        raise RuntimeError(f"Embedding request failed: {str(e)}")


def batch_embed(
    texts: list[str],
    input_type: InputType = "passage",
    batch_size: int = 10,
) -> list[list[float]]:

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        embeddings = get_embedding(batch, input_type)

        all_embeddings.extend(embeddings)

    return all_embeddings