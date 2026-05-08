from abc import ABC, abstractmethod
from embedding_Service.Model.Schemas import IndexRequest, IndexResponse


class IEmbeddingService(ABC):

    @abstractmethod
    async def save_embeddings(self, request: IndexRequest) -> IndexResponse:
        """
        Recibe los chunks de un documento, genera sus embeddings
        y los indexa en Qdrant.
        """
        pass
