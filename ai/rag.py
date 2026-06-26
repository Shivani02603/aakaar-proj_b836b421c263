import os
from .embeddings import get_embedding
import asyncpg
import openai

async def retrieve_context(query: str, top_k: int, session_id: str, user_id: str):
    embedding = await get_embedding(query)
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    try:
        rows = await conn.fetch(
            """
            SELECT chunk_text, metadata, embedding <-> $1 AS distance
            FROM document_chunks
            WHERE session_id = $2 AND user_id = $3
            ORDER BY distance ASC
            LIMIT $4
            """,
            embedding, session_id, user_id, top_k
        )
        return rows
    finally:
        await conn.close()

async def answer_question(query: str, session_id: str, user_id: str) -> dict:
    context_chunks = await retrieve_context(query, top_k=5, session_id=session_id, user_id=user_id)
    if not context_chunks:
        return {"answer": "No relevant context found.", "sources": []}

    prompt_context = "\n\n".join([chunk["chunk_text"] for chunk in context_chunks])
    prompt = f"Answer the following question based on the context below:\n\nContext:\n{prompt_context}\n\nQuestion:\n{query}"

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content

    sources = [
        {"filename": chunk["metadata"]["source_filename"], "location": chunk["metadata"]["page_or_row"]}
        for chunk in context_chunks
    ]

    return {"answer": answer, "sources": sources}