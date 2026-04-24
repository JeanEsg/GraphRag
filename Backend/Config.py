from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Base de datos vectorial ────────────────────────────────────────────────
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "graphrag_chunks"
    embedding_dimension: int = 384          
    fastembed_model_name: str = "BAAI/bge-small-en-v1.5"
    fastembed_max_tokens: int = 512

    # ── Base de datos de grafos ────────────────────────────────────────────────
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # ── Chunking ───────────────────────────────────────────────────────────────
    chunk_size: int = 512
    chunk_overlap: int = 64

    # ── Seguridad / gateway ────────────────────────────────────────────────────
    app_env: str = "development"
    upload_dir: str = "uploads"
    max_file_size_mb: int = 10
    allowed_extensions: str = "pdf,docx,txt"

    # ── spaCy ─────────────────────────────────────────────────────────────────
    spacy_model: str = "es_core_news_sm"  

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    class Config:
        env_file = ".env"


settings = Settings()
