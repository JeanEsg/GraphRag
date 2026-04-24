from pydantic import BaseModel


# ── Response al Orchestrator ───────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    document_id: str
    message: str
