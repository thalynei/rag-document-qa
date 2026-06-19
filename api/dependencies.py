from __future__ import annotations

from functools import lru_cache

from rag.embeddings import get_embeddings


@lru_cache(maxsize=1)
def get_cached_embeddings():
    return get_embeddings()
