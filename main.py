"""
AEKA — Enterprise Knowledge Assistant
FastAPI Backend
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime

from document_processor import DocumentProcessor
from vector_store import VectorStore
from llm_handler import LLMHandler

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AEKA API",
    description="Enterprise Knowledge Assistant — RAG + Vector DB + LLM",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Singletons
doc_processor = DocumentProcessor()
vector_store = VectorStore()
llm_handler = LLMHandler()

# ── Request / Response Models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    model: str = "mistral"
    top_k: int = 4
    use_knowledge_base: bool = True

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    model_used: str
    query: str

class DeleteDocumentRequest(BaseModel):
    filename: str

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "AEKA API running", "version": "1.0.0"}


@app.get("/health")
def health():
    ollama_ok = llm_handler.check_connection()
    return {
        "api": "online",
        "ollama": "online" if ollama_ok else "offline",
        "available_models": llm_handler.list_models() if ollama_ok else []
    }


# ── Documents ─────────────────────────────────────────────────────────────────

@app.post("/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        if not file.filename.endswith((".pdf", ".docx")):
            results.append({"file": file.filename, "status": "error", "message": "Unsupported format. Use PDF or DOCX."})
            continue

        try:
            tmp_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
            with open(tmp_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            chunks = doc_processor.process_file(str(tmp_path), file.filename)

            if not chunks:
                results.append({"file": file.filename, "status": "error", "message": "No text could be extracted."})
                continue

            vector_store.add_documents(chunks, file.filename)
            results.append({
                "file": file.filename,
                "status": "success",
                "chunks": len(chunks),
                "message": f"Processed {len(chunks)} chunks"
            })

        except Exception as e:
            results.append({"file": file.filename, "status": "error", "message": str(e)})

    return {"results": results}


@app.get("/documents")
def list_documents():
    docs = vector_store.get_all_documents()
    return {"documents": docs, "total": len(docs)}


@app.get("/documents/stats")
def get_stats():
    return {
        "document_count": vector_store.get_document_count(),
        "chunk_count": vector_store.get_chunk_count(),
        "documents": vector_store.get_all_documents()
    }


@app.delete("/documents/{filename}")
def delete_document(filename: str):
    try:
        vector_store.delete_document(filename)
        return {"status": "success", "message": f"'{filename}' removed from knowledge base."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents")
def clear_all_documents():
    vector_store.clear_all()
    return {"status": "success", "message": "Knowledge base cleared."}


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not llm_handler.check_connection():
        raise HTTPException(status_code=503, detail="Ollama is not running. Please start it with: ollama serve")

    sources = []
    context = ""

    if request.use_knowledge_base:
        retrieved = vector_store.similarity_search(request.query, k=request.top_k)
        if retrieved:
            context = "\n\n---\n\n".join([r["text"] for r in retrieved])
            sources = retrieved

    answer = llm_handler.generate_response(
        query=request.query,
        context=context,
        model=request.model,
        use_context=request.use_knowledge_base and bool(context)
    )

    return ChatResponse(
        answer=answer,
        sources=sources,
        model_used=request.model,
        query=request.query
    )


@app.get("/models")
def get_models():
    available = llm_handler.list_models()
    all_models = [
        {"id": "mistral", "name": "Mistral 7B", "description": "Best quality, balanced speed", "size": "4.1 GB"},
        {"id": "llama3", "name": "Llama 3 8B", "description": "Excellent reasoning, slightly heavy", "size": "4.7 GB"},
        {"id": "phi3", "name": "Phi-3 Mini", "description": "Ultra fast, laptop-friendly", "size": "2.2 GB"},
        {"id": "gemma2", "name": "Gemma 2B", "description": "Lightweight and quick", "size": "1.6 GB"},
    ]
    for m in all_models:
        m["available"] = any(m["id"] in a for a in available)
    return {"models": all_models}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
