import logging
import uuid
import asyncio
from typing import List

from fastapi import HTTPException, status

from Config import settings
from document_Service.Model.Schemas import DocumentUploadResponse
from embedding_Service.Model.Schemas import IndexRequest
from indexer_Service.Model.Schemas import (
    ChunkPayload as IndexerChunkPayload,
    IndexerRequest,
)
from document_Service.Repository.DocumentRepository import DocumentRepository
from document_Service.Service.IDocumentService import IDocumentService
from embedding_Service.Service.IEmbeddingService import IEmbeddingService
from indexer_Service.Service.IIndexerService import IIndexerService
from document_Service.Service.Extraction_Strategies import (
    PDFExtractionStrategy,
    DocxExtractionStrategy,
    TxtExtractionStrategy,
)

logger = logging.getLogger(__name__)

STRATEGIES = {
    "pdf": PDFExtractionStrategy(),
    "docx": DocxExtractionStrategy(),
    "txt": TxtExtractionStrategy(),
}


class DocumentService(IDocumentService):

    def __init__(
        self,
        document_repository: DocumentRepository,
        embedding_service: IEmbeddingService,
        indexer_service: IIndexerService,
    ):
        self._document_repo = document_repository
        self._embedding_service = embedding_service
        self._indexer_service = indexer_service

    async def process_document(
        self,
        filename: str,
        content_type: str | None,
        file_content: bytes,
    ) -> DocumentUploadResponse:
        # 1. Obtener extensión y validar
        extension = self._get_extension(filename)
        strategy = STRATEGIES.get(extension)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Tipo de archivo '{extension}' no soportado.",
            )

        # 2. Guardar archivo y generar ID
        document_id = str(uuid.uuid4())
        file_path = await self.save_file(
            filename=filename,
            file_content=file_content,
            document_id=document_id,
        )
        logger.info("Archivo guardado en: %s", file_path)

        # 3. Extraer texto
        content = strategy.extract_content(file_path)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se pudo extraer texto del documento.",
            )
        logger.info("Texto extraído: %d caracteres", len(content))

        # 4. Dividir en chunks
        chunks = self._chunk_content(content)
        logger.info("Chunks generados: %d", len(chunks))

        # 5. Enviar al embedding e indexer
        await self.send_chunks(
            document_id=document_id,
            filename=filename,
            chunks=chunks,
        )
        logger.info("Chunks enviados a Embedding e Indexer")

        return DocumentUploadResponse(
            message="Documento procesado correctamente.",
            document_id=document_id,
        )

    async def save_file(self, filename: str, file_content: bytes, document_id: str) -> str:
        file_path = await self._document_repo.save_file(
            filename=filename,
            file_content=file_content,
            document_id=document_id,
        )
        return file_path

    async def send_chunks(self, document_id: str, filename: str, chunks: list[str]) -> None:
        embedding_task = self._embedding_service.save_embeddings(
            IndexRequest(
                document_id=document_id,
                filename=filename,
                chunks=chunks,
            )
        )

        indexer_chunks = [
            IndexerChunkPayload(
                chunk_id=f"{document_id}-{index:04d}",
                chunk_index=index,
                text=chunk,
            )
            for index, chunk in enumerate(chunks)
        ]

        indexer_task = self._indexer_service.process_chunks(
            IndexerRequest(
                document_id=document_id,
                filename=filename,
                chunks=indexer_chunks,
            )
        )
        await asyncio.gather(
            embedding_task,
            indexer_task,
    )

    def _chunk_content(self, content: str) -> List[str]:
        size = settings.chunk_size
        overlap = settings.chunk_overlap
        chunks = []
        start = 0
        while start < len(content):
            end = start + size
            chunks.append(content[start:end])
            start += size - overlap
        return chunks

    @staticmethod
    def _get_extension(filename: str) -> str:
        parts = filename.rsplit(".", 1)
        if len(parts) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no tiene extensión.",
            )
        return parts[1].lower()
