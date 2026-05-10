import os
import re
import logging
from typing import Any
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_base: str | None = None
_headers: dict[str, str] |None = None


def _extract_project_ref(host: str) -> str | None:
    """
    Supports:
      db.<ref>.supabase.co
      db.<ref>.supabase.net
      <ref>.supabase.co
    """

    host = host.lower()

    patterns = [
        r"db\.([a-z0-9-]+)\.supabase\.co",
        r"db\.([a-z0-9-]+)\.supabase\.net",
        r"([a-z0-9-]+)\.supabase\.co",
    ]

    for pattern in patterns:

        match = re.fullmatch(pattern, host)

        if match:
            return match.group(1)

    return None


def _infer_rest_url_from_postgres_dsn(
    dsn: str,
) -> str | None:
    """
    Convert postgres DSN into:
    https://<project-ref>.supabase.co
    """

    try:

        parsed = urlparse(
            dsn.replace(
                "postgres://",
                "postgresql://",
                1,
            )
        )

    except Exception:
        return None

    host = parsed.hostname or ""

    ref = _extract_project_ref(host)

    if ref:
        return f"https://{ref}.supabase.co"

    return None


def _hydrate_supabase_url_from_database_urls() -> None:
    """
    If SUPABASE_URL is missing,
    infer it from DB URLs.
    """

    if os.environ.get("SUPABASE_URL"):
        return

    for key in (
        "DATABASE_URL",
        "POSTGRES_URL",
        "SUPABASE_DB_URL",
        "POSTGRES_PRISMA_URL",
    ):

        raw = os.environ.get(key)

        if not raw:
            continue

        inferred = _infer_rest_url_from_postgres_dsn(raw)

        if inferred:
            os.environ["SUPABASE_URL"] = inferred
            return


def _normalize_supabase_url_if_postgres_dsn() -> None:
    """
    If SUPABASE_URL accidentally contains
    a postgres DSN, normalize it.
    """

    raw = (
        os.environ.get("SUPABASE_URL") or ""
    ).strip()

    if not raw.lower().startswith("postgres"):
        return

    inferred = _infer_rest_url_from_postgres_dsn(raw)

    if inferred:
        os.environ["SUPABASE_URL"] = inferred
        return

    raise RuntimeError(
        "Could not infer SUPABASE_URL from Postgres DSN.\n"
        "Expected:\n"
        "SUPABASE_URL=https://<project-ref>.supabase.co"
    )


def connect_db() -> None:

    global _base, _headers

    _hydrate_supabase_url_from_database_urls()

    _normalize_supabase_url_if_postgres_dsn()

    missing = [
        key
        for key in (
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
        )
        if not os.environ.get(key)
    ]

    if missing:

        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}"
        )

    url = os.environ["SUPABASE_URL"].rstrip("/")

    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

    _base = url

    _headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    logger.info("Supabase connection initialized")


def _ensure_connection() -> None:

    global _base, _headers

    if not _base or not _headers:
        connect_db()


# ---------------------------------------------------
# INSERT CHUNKS
# ---------------------------------------------------

def insert_chunks(
    chunks: list[dict[str, Any]],
) -> Any:
    """
    Insert chunks into Supabase table.
    """

    _ensure_connection()

    response = httpx.post(
        f"{_base}/rest/v1/chunks",
        headers={
            **_headers,
            "Prefer": "return=representation",
        },
        json=chunks,
        timeout=60,
    )

    print("INSERT STATUS:", response.status_code)
    print("INSERT BODY:", response.text)

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------
# FETCH CHUNKS
# ---------------------------------------------------

def fetch_chunks(limit: int = 10) -> Any:
    """
    Fetch chunks from Supabase.
    """

    _ensure_connection()

    response = httpx.get(
        f"{_base}/rest/v1/chunks"
        f"?select=*&limit={limit}",
        headers=_headers,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------
# DELETE CHUNK
# ---------------------------------------------------

def delete_chunk(chunk_id: str) -> Any:
    """
    Delete chunk by ID.
    """

    _ensure_connection()

    response = httpx.delete(
        f"{_base}/rest/v1/chunks?id=eq.{chunk_id}",
        headers=_headers,
        timeout=30,
    )

    response.raise_for_status()

    return {
        "success": True,
        "deleted_id": chunk_id,
    }


# ---------------------------------------------------
# VECTOR SEARCH RPC
# ---------------------------------------------------

def rpc_match_chunks(
    query_embedding: list[float],
    match_count: int = 5,
    filter_doc_id: str | None = None,
) -> Any:
    """
    Call Supabase pgvector RPC function.
    """

    _ensure_connection()

    payload = {
        "query_embedding": query_embedding,
        "match_count": match_count,
        "filter_doc_id": filter_doc_id,
    }

    response = httpx.post(
        f"{_base}/rest/v1/rpc/match_chunks",
        headers=_headers,
        json=payload,
        timeout=60,
    )

    print("RPC STATUS:", response.status_code)
    print("RPC BODY:", response.text)

    response.raise_for_status()

    return response.json()