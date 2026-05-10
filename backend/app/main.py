import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.db import connect_db
from app.routes import ingest, query

# Default load_dotenv() only reads cwd — often `backend/` while `.env` lives in repo root.
_backend_dir = Path(__file__).resolve().parent.parent
_repo_root = _backend_dir.parent
load_dotenv(_repo_root / ".env")
load_dotenv(_backend_dir / ".env", override=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    connect_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/api")
app.include_router(query.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


def run():
    import uvicorn

    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
