import logging
from indexer_Service.Model.Schemas import IndexerRequest, IndexerResponse
from indexer_Service.Infra.Spacy_Client import SpacyNERProvider
from indexer_Service.Repository.GraphRepository import GraphRepository
from indexer_Service.Service.IIndexerService import IIndexerService

logger = logging.getLogger(__name__)


class IndexerService(IIndexerService):

    def __init__(
        self,
        graph_repository: GraphRepository,
        spacy_client: SpacyNERProvider,
    ):
        self._repo = graph_repository
        self._spacy = spacy_client

    async def process_chunks(self, request: IndexerRequest) -> IndexerResponse:
        logger.info(
            "Indexando grafo '%s' | %d chunks",
            request.document_id,
            len(request.chunks),
        )

        total_entities = 0

        # 1. Crear nodo Document
        self._repo.upsert_document(
            document_id=request.document_id,
            filename=request.filename,
        )

        # 2. Procesar cada chunk
        for chunk in request.chunks:
            # Crear nodo Chunk + relación HAS_CHUNK
            self._repo.upsert_chunk(
                document_id=request.document_id,
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
            )

            # Extraer entidades y crear relaciones MENTIONS
            entities = self._spacy.extract(chunk.text)
            for entity in entities:
                self._repo.upsert_entity_and_link(
                    chunk_id=chunk.chunk_id,
                    entity_text=entity[0],
                    entity_label=entity[1],
                )
            total_entities += len(entities)
            logger.debug("Chunk %d: %d entidades", chunk.chunk_index, len(entities))

        # 3. Crear relaciones NEXT_CHUNK entre chunks consecutivos
        sorted_chunks = sorted(request.chunks, key=lambda c: c.chunk_index)
        for i in range(len(sorted_chunks) - 1):
            self._repo.link_consecutive_chunks(
                chunk_id_current=sorted_chunks[i].chunk_id,
                chunk_id_next=sorted_chunks[i + 1].chunk_id,
            )

        logger.info(
            "Grafo indexado: %d chunks, %d entidades",
            len(request.chunks),
            total_entities,
        )

        return IndexerResponse(
            message="Grafo indexado correctamente.",
            document_id=request.document_id,
            chunks_processed=len(request.chunks),
            entities_found=total_entities,
        )
