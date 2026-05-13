import logging

from document_Service.Model.Schemas import DocumentUploadResponse
from orchestrator_Service.Service.IOrchestratorService import IOrchestratorService
from document_Service.Service.IDocumentService import IDocumentService
from question_Service.Service.QuestionService import QuestionService
from question_Service.Model.Schemas import QuestionRequest, QuestionResponse
logger = logging.getLogger(__name__)


class OrchestratorService(IOrchestratorService):

    def __init__(self, document_service: IDocumentService, question_service: QuestionService = None):
        self._document_service = document_service
        self._question_service = question_service

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

    async def ask_question(self, request: QuestionRequest) -> QuestionResponse:
        logger.info("Orquestando pregunta...")
        if not self._question_service:
            raise Exception("QuestionService no inyectado")
        return await self._question_service.ask_question(request)

