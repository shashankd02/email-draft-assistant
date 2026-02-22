from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import chromadb

from src.core.config import settings


@dataclass
class MemoryHit:
    text: str
    source: str


class VectorMemoryService:
    def __init__(self) -> None:
        self.client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            tenant=settings.chroma_tenant,
            database=settings.chroma_database,
        )
        self.profile_collection = self.client.get_or_create_collection("profile_memories")
        self.style_collection = self.client.get_or_create_collection("style_preferences")

    def get_profile_context(self, user_id: str, query: str, limit: int = 3) -> list[MemoryHit]:
        try:
            result = self.profile_collection.query(
                query_texts=[query],
                n_results=limit,
                where={"user_id": user_id},
            )
            docs = (result.get("documents") or [[]])[0]
            metas = (result.get("metadatas") or [[]])[0]
            hits = []
            for idx, doc in enumerate(docs):
                source = "profile"
                if idx < len(metas) and metas[idx]:
                    source = str(metas[idx].get("source", "profile"))
                hits.append(MemoryHit(text=str(doc), source=source))
            return hits
        except Exception:
            return []

    def upsert_profile_memory(self, user_id: str, text: str, source: str = "feedback") -> None:
        try:
            self.profile_collection.add(
                ids=[str(uuid4())],
                documents=[text],
                metadatas=[{"user_id": user_id, "source": source}],
            )
        except Exception:
            # Non-blocking memory path.
            return

    def upsert_style_preference(self, user_id: str, text: str) -> None:
        try:
            self.style_collection.add(
                ids=[str(uuid4())],
                documents=[text],
                metadatas=[{"user_id": user_id, "source": "style_preference"}],
            )
        except Exception:
            return

    def is_available(self) -> bool:
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False


_service: VectorMemoryService | None = None


class NullVectorMemoryService(VectorMemoryService):
    def __init__(self) -> None:  # pragma: no cover
        pass

    def get_profile_context(self, user_id: str, query: str, limit: int = 3) -> list[MemoryHit]:
        _ = user_id
        _ = query
        _ = limit
        return []

    def upsert_profile_memory(self, user_id: str, text: str, source: str = "feedback") -> None:
        _ = user_id
        _ = text
        _ = source

    def upsert_style_preference(self, user_id: str, text: str) -> None:
        _ = user_id
        _ = text

    def is_available(self) -> bool:
        return False


def get_vector_memory_service() -> VectorMemoryService:
    global _service
    if _service is None:
        try:
            _service = VectorMemoryService()
        except Exception:
            _service = NullVectorMemoryService()
    return _service
