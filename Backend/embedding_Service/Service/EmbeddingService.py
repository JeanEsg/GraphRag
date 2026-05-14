import logging
from fastapi import HTTPException, status
from embedding_Service.Model.Schemas import IndexRequest, IndexResponse
from embedding_Service.Infra.FastEmbedClient import FastEmbedClient
from embedding_Service.Repository.EmbeddingRepository import EmbeddingRepository
from embedding_Service.Service.IEmbeddingService import IEmbeddingService

logger = logging.getLogger(__name__)


class EmbeddingService(IEmbeddingService):

    def __init__(
        self,
        embedding_repository: EmbeddingRepository,
        fastembed_client: FastEmbedClient,
    ):
        self._repo = embedding_repository
        self._fastembed = fastembed_client

    async def save_embeddings(self, request: IndexRequest) -> IndexResponse:
        logger.info(
            "Procesando documento '%s' | %d chunks recibidos",
            request.document_id,
            len(request.chunks),
        )

        if not request.chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se recibieron chunks para indexar.",
            )

        # 1. Validar que los chunks no superen el límite de tokens del modelo
        valid_indices = [
            i for i, chunk in enumerate(request.chunks)
            if self._fastembed.count_tokens(chunk) <= self._fastembed._max_tokens
        ]

        if not valid_indices:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Todos los chunks superan el límite de tokens del modelo.",
            )

        valid_chunks = [request.chunks[i] for i in valid_indices]
        valid_ids = [request.chunk_ids[i] for i in valid_indices]

        logger.info(
            "%d/%d chunks válidos tras validación de tokens",
            len(valid_chunks),
            len(request.chunks),
        )

        # 2. Generar embeddings (FastEmbed tokeniza internamente aquí)
        vectors = self._fastembed.embed(valid_chunks)
        logger.info("Embeddings generados: %d vectores de dimensión %d", len(vectors), len(vectors[0]))

        # 3. Persistir en Qdrant
        self._repo.upsert_points(
            document_id=request.document_id,
            filename=request.filename,
            chunks=valid_chunks,
            chunk_ids=valid_ids,
            vectors=vectors,
        )

        return IndexResponse(
            message="Chunks indexados correctamente.",
            document_id=request.document_id,
            chunks_indexed=len(vectors),
            chunks_discarded=len(request.chunks) - len(valid_chunks),
        )
