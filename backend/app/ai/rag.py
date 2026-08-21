import chromadb
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger


class RAGEngine:
    def __init__(self, persist_dir: Path | None = None):
        self._persist_dir = persist_dir or settings.chroma_dir
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._client = chromadb.PersistentClient(path=str(self._persist_dir))
            self._collection = self._client.get_or_create_collection(
                name="perf_knowledge",
                metadata={"hnsw:space": "cosine"},
            )
            self._available = True
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}")
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    async def index_document(self, doc_id: str, text: str, metadata: dict | None = None) -> int:
        if not self._available:
            return 0
        chunks = self._chunk_text(text)
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        meta_list = [metadata or {} for _ in chunks]

        self._collection.upsert(documents=chunks, ids=ids, metadatas=meta_list)
        logger.info(f"Indexed {len(chunks)} chunks for document {doc_id}")
        return len(chunks)

    async def retrieve(self, query: str, n_results: int = 5) -> list[str]:
        if not self._available:
            return []
        try:
            results = self._collection.query(query_texts=[query], n_results=n_results)
            return results["documents"][0] if results["documents"] else []
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []

    async def delete_document(self, doc_id: str) -> None:
        if not self._available:
            return
        existing = self._collection.get(where={"doc_id": doc_id})
        if existing["ids"]:
            self._collection.delete(ids=existing["ids"])

    def get_stats(self) -> dict:
        if not self._available:
            return {"status": "unavailable", "count": 0}
        return {"status": "healthy", "count": self._collection.count()}


rag_engine = RAGEngine()
