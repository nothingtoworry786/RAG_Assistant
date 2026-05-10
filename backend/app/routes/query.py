import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.config.db import rpc_match_chunks
from app.services.embedding_service import get_embedding
from app.services.groq_service import get_llm_response

router = APIRouter()


class QueryBody(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    doc_id: str = Field(
        alias="docId",
        min_length=1,
    )

    question: str = Field(
        min_length=1,
    )


@router.post("/query")
async def query(body: QueryBody):

    try:

        # -------------------------------------------------
        # CREATE QUERY EMBEDDING
        # -------------------------------------------------

        query_vector = get_embedding(
            body.question,
            "query",
        )

        # -------------------------------------------------
        # VECTOR SEARCH
        # -------------------------------------------------

        raw = rpc_match_chunks(
            query_vector,
            filter_doc_id=body.doc_id,
            match_count=8,
        )

        # -------------------------------------------------
        # FILTER + SORT RESULTS
        # -------------------------------------------------

        results = sorted(
            [
                {
                    "text": r["chunk_text"],
                    "pageNumber": r["page_number"],
                    "score": r.get("score", 0),
                }
                for r in raw
                if r.get("score", 0) > 0.50
            ],
            key=lambda x: x["score"],
            reverse=True,
        )[:5]

        # -------------------------------------------------
        # NO RESULTS
        # -------------------------------------------------

        if not results:

            return {
                "answer": (
                    "I couldn't find relevant content "
                    "in the document to answer your question."
                ),
                "sources": [],
            }

        # -------------------------------------------------
        # BUILD CONTEXT
        # -------------------------------------------------

        context_parts = []

        for r in results:

            context_parts.append(
                f"""
Source Page: {r['pageNumber']}

Content:
{r['text']}
"""
            )

        context = "\n\n---\n\n".join(context_parts)

        # -------------------------------------------------
        # IMPROVED RAG PROMPT
        # -------------------------------------------------

        prompt = f"""
You are an expert document analysis assistant.

Answer the user's question ONLY using the provided document context.

Instructions:
- Give clear, accurate, and detailed answers.
- Write in complete paragraphs.
- Use bullet points when helpful.
- Synthesize information from multiple sections.
- Cite page numbers naturally in the answer.
- Do NOT mention chunks.
- Do NOT use outside knowledge.
- If the answer is incomplete in the document,
  clearly say so.
- Keep answers professional and concise.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{body.question}
"""

        # -------------------------------------------------
        # GENERATE ANSWER
        # -------------------------------------------------

        answer = get_llm_response(prompt)

        # -------------------------------------------------
        # SOURCES
        # -------------------------------------------------

        sources = [
            {
                "pageNumber": r["pageNumber"],
                "score": round(r["score"], 3),
                "excerpt": r["text"][:160] + "...",
            }
            for r in results
        ]

        return {
            "answer": answer,
            "sources": sources,
        }

    except RuntimeError as err:

        print("Query error:", err)

        traceback.print_exc()

        if str(err) == "LLM_MODEL_OVERLOADED":

            return JSONResponse(
                status_code=503,
                content={
                    "error": (
                        "AI model is temporarily overloaded. "
                        "Please try again."
                    )
                },
            )

        return JSONResponse(
            status_code=500,
            content={"error": str(err)},
        )

    except Exception as err:

        print("Query error:", err)

        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={"error": str(err)},
        )