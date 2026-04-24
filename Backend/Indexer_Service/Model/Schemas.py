from pydantic import BaseModel


class ChunkPayload(BaseModel):
    chunk_id: str
    chunk_index: int
    text: str


class IndexerRequest(BaseModel):
    document_id: str
    filename: str
    chunks: list[ChunkPayload]


class IndexerResponse(BaseModel):
    message: str
    document_id: str
    chunks_processed: int
    entities_found: int
