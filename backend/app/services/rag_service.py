"""
RAGService — pgvector similarity search.

Retrieves relevant knowledge-base chunks for a given query.
Implemented in ST-07.
"""


class RAGService:
    """
    Provides retrieve(query, top_k, metadata_filter) -> list[dict].
    Implemented in ST-07.
    """

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: dict | None = None,
    ) -> list[dict]:
        raise NotImplementedError("RAGService implemented in ST-07")
