from pydantic import BaseModel, Field
from typing import List, Dict, Any

class QuestionRequest(BaseModel):
    query: str = Field(..., description="Pregunta del usuario")
    limit: int = Field(5, description="Cantidad máxima de chunks a recuperar por cada fuente")

class RetrievedChunk(BaseModel):
    chunk_id: str
    text: str
    source: str  # 'vector' o 'graph'
    score: float | None = None
    metadata: Dict[str, Any] = {}

class QuestionResponse(BaseModel):
    query: str
    answer: str
    chunks: List[RetrievedChunk]
