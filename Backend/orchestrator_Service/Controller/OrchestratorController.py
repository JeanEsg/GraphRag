import logging

from fastapi import APIRouter, Depends, File, Request, UploadFile

from orchestrator_Service.Model.Schemas import DocumentUploadResponse
from orchestrator_Service.Security.File_Validator import validate_file
from orchestrator_Service.Service.IOrchestratorService import IOrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Orchestrator"])


def get_orchestrator_service(request: Request) -> IOrchestratorService:
    return request.app.state.orchestrator_service



# ── Ingesta de documentos ──────────────────────────────────

@router.post(
    "/orchestrator/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
    summary="Ingesta de documento",
    description="Recibe un documento, lo valida y lo delega al Document Service.",
)
async def upload_document(
    file: UploadFile = File(..., description="Archivo a ingestar (pdf, docx, txt)"),
    service: IOrchestratorService = Depends(get_orchestrator_service),
):

    file_content = await validate_file(file)

    return await service.send_document(
        filename=file.filename,
        content_type=file.content_type,
        file_content=file_content,
    )
