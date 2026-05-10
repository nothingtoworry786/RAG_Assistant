import traceback
import uuid

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.config.db import insert_chunks
from app.services.chunker import chunk_text
from app.services.embedding_service import batch_embed
from app.services.pdf_parser import parse_pdf, parse_txt

router = APIRouter()

INSERT_BATCH = 200


@router.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    try:
        if not file.filename:
            return JSONResponse(status_code=400, content={"error": "No file uploaded"})

        buf = await file.read()
        if not buf:
            return JSONResponse(status_code=400, content={"error": "No file uploaded"})

        name = file.filename
        ctype = (file.content_type or "").lower()
        is_pdf = ctype == "application/pdf" or name.lower().endswith(".pdf")
        is_txt = ctype == "text/plain" or name.lower().endswith(".txt")

        if not is_pdf and not is_txt:
            return JSONResponse(
                status_code=400,
                content={"error": "Only PDF and TXT files are supported"},
            )

        pages = parse_pdf(buf) if is_pdf else parse_txt(buf)

        raw_chunks: list[dict] = []
        for page in pages:
            page_number = page["pageNumber"]
            text = page["text"]
            for chunk in chunk_text(text):
                raw_chunks.append({"text": chunk, "pageNumber": page_number})

        if not raw_chunks:
            return JSONResponse(
                status_code=422,
                content={"error": "No text could be extracted from the file"},
            )

        texts = [c["text"] for c in raw_chunks]
        embeddings = batch_embed(texts, "passage")

        doc_id = str(uuid.uuid4())
        rows = [
            {
                "doc_id": doc_id,
                "filename": name,
                "chunk_text": raw_chunks[i]["text"],
                "embedding": embeddings[i],
                "page_number": raw_chunks[i]["pageNumber"],
                "chunk_index": i,
            }
            for i in range(len(raw_chunks))
        ]

        for i in range(0, len(rows), INSERT_BATCH):
            insert_chunks(rows[i : i + INSERT_BATCH])

        return {"docId": doc_id, "filename": name, "chunkCount": len(rows)}
    except Exception as err:
        print("Ingest error:", err)
        traceback.print_exc()
        return JSONResponse(
            status_code=500, content={"error": str(err)}
        )
