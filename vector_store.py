"""Vector Store — ChromaDB with sentence-transformers embeddings"""

import os
from typing import List, Dict
from datetime import datetime

CHROMA_DIR = "./chroma_db"
COLLECTION = "aeka_knowledge"
EMBED_MODEL = "all-MiniLM-L6-v2"


class VectorStore:
    def __init__(self):
        self._col = None
        self._embedder = None
        self._init()

    def _init(self):
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            os.makedirs(CHROMA_DIR, exist_ok=True)
            client = chromadb.PersistentClient(path=CHROMA_DIR)
            self._col = client.get_or_create_collection(
                name=COLLECTION,
                metadata={"hnsw:space": "cosine"}
            )
            self._embedder = SentenceTransformer(EMBED_MODEL)
            print(f"[VectorStore] Ready — {self._col.count()} chunks loaded")
        except Exception as e:
            print(f"[VectorStore] Init error: {e}")

    def add_documents(self, chunks: List[Dict], source_file: str):
        if not self._col or not self._embedder:
            return
        texts = [c["text"] for c in chunks]
        embeddings = self._embedder.encode(texts, show_progress_bar=False).tolist()
        ids = [f"{source_file}__chunk_{c['chunk_id']}" for c in chunks]
        metadatas = [
            {
                "file": c["file"],
                "chunk_id": c["chunk_id"],
                "ingested_at": datetime.now().isoformat()
            }
            for c in chunks
        ]
        self._col.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    def similarity_search(self, query: str, k: int = 4) -> List[Dict]:
        if not self._col or not self._embedder or self._col.count() == 0:
            return []
        q_emb = self._embedder.encode([query]).tolist()
        results = self._col.query(
            query_embeddings=q_emb,
            n_results=min(k, self._col.count()),
            include=["documents", "metadatas", "distances"]
        )
        out = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            out.append({
                "text": doc,
                "file": meta.get("file", "unknown"),
                "chunk_id": meta.get("chunk_id", 0),
                "ingested_at": meta.get("ingested_at", ""),
                "score": round(1 - dist, 4)
            })
        return out

    def get_all_documents(self) -> List[Dict]:
        if not self._col or self._col.count() == 0:
            return []
        results = self._col.get(include=["metadatas"])
        seen = {}
        for meta in results["metadatas"]:
            f = meta.get("file", "unknown")
            if f not in seen:
                seen[f] = {
                    "filename": f,
                    "chunk_count": 0,
                    "ingested_at": meta.get("ingested_at", ""),
                    "type": "pdf" if f.lower().endswith(".pdf") else "docx"
                }
            seen[f]["chunk_count"] += 1
        return list(seen.values())

    def delete_document(self, filename: str):
        if not self._col:
            return
        results = self._col.get(include=["metadatas"])
        ids_to_delete = [
            results["ids"][i]
            for i, meta in enumerate(results["metadatas"])
            if meta.get("file") == filename
        ]
        if ids_to_delete:
            self._col.delete(ids=ids_to_delete)

    def get_document_count(self) -> int:
        docs = self.get_all_documents()
        return len(docs)

    def get_chunk_count(self) -> int:
        if not self._col:
            return 0
        return self._col.count()

    def clear_all(self):
        if self._col:
            try:
                import chromadb
                os.makedirs(CHROMA_DIR, exist_ok=True)
                client = chromadb.PersistentClient(path=CHROMA_DIR)
                client.delete_collection(COLLECTION)
                self._col = client.get_or_create_collection(
                    name=COLLECTION,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                print(f"[VectorStore] Clear error: {e}")
