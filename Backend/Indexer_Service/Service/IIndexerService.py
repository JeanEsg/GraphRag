from abc import ABC, abstractmethod
from Indexer_Service.Model.Schemas import IndexerRequest, IndexerResponse


class IIndexerService(ABC):

    @abstractmethod
    async def process_chunks(self, request: IndexerRequest) -> IndexerResponse:
        """
        Recibe chunks, aplica NER e indexa el grafo en Neo4j.
        """
        pass
