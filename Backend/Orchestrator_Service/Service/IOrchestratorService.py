from abc import ABC, abstractmethod

from Orchestrator_Service.Model.Schemas import DocumentUploadResponse


class IOrchestratorService(ABC):

    @abstractmethod
    async def send_document(
        self, filename: str, content_type: str, file_content: bytes) -> DocumentUploadResponse:
        """
        Orquesta la ingesta de un documento.
        """
        pass