import logging

from document_Service.Model.Schemas import DocumentUploadResponse
from orchestrator_Service.Service.IOrchestratorService import IOrchestratorService
from document_Service.Service.IDocumentService import IDocumentService
logger = logging.getLogger(__name__)


class OrchestratorService(IOrchestratorService):

    def __init__(self, document_service: IDocumentService):
        self._document_service = document_service

    async def send_document(
        self,
        filename: str,
        content_type: str,
        file_content: bytes,
    ) -> DocumentUploadResponse:
        logger.info("Iniciando Envio de documento: %s", filename)
        result = await self._document_service.process_document(
            filename=filename,
            content_type=content_type,
            file_content=file_content,
        )
        logger.info("Documento ingresado correctamente. ID: %s", result.document_id)
        return result
