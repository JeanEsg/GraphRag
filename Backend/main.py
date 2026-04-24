import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI

from Config import settings

# ── Clientes de infraestructura ──────────────────────────────────────────────────────
from Embedding_Service.Infra.Qdrant_Client import get_qdrant_client
from Indexer_Service.Infra.Neo4j_Client import get_neo4j_driver

# ── Document ───────────────────────────────────────────────────────────────────
from Document_Service.Repository.DocumentRepository import DocumentRepository
from Document_Service.Service.DocumentService import DocumentService

# ── Embedding ─────────────────────────────────────────────────────────────────
from Embedding_Service.Repository.EmbeddingRepository import EmbeddingRepository
from Embedding_Service.Service.EmbeddingService import EmbeddingService
from Embedding_Service.Infra.FastEmbedClient import FastEmbedClient

# ── Indexer ───────────────────────────────────────────────────────────────────
from Indexer_Service.Repository.GraphRepository import GraphRepository
from Indexer_Service.Service.Indexer_Service import IndexerService
from Indexer_Service.Infra.Spacy_Client import SpacyNERProvider

# ── Orchestrator ───────────────────────────────────────────────────────────────
from Orchestrator_Service.Controller.OrchestratorController import router as orchestrator_router
from Orchestrator_Service.Service.OrchestratorService import OrchestratorService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando GraphRAG")

    # Clientes de infraestructura
    qdrant = get_qdrant_client()
    neo4j = get_neo4j_driver()

    # Módulo Embedding
    embedding_provider = FastEmbedClient(
        model_name=settings.fastembed_model_name,
        max_tokens=settings.fastembed_max_tokens,
    )
    embedding_repo = EmbeddingRepository(
        client=qdrant,
        collection_name=settings.qdrant_collection,
        vector_size=embedding_provider.vector_size,
    )
    embedding_service = EmbeddingService(
        embedding_repository=embedding_repo,
        fastembed_client=embedding_provider,
    )

    # Módulo Indexer
    ner_provider = SpacyNERProvider(model_name=settings.spacy_model)
    indexer_repo = GraphRepository(driver=neo4j)
    indexer_service = IndexerService(
        graph_repository=indexer_repo,
        spacy_client=ner_provider,
    )

    # Módulo Document
    document_repo = DocumentRepository()
    document_service = DocumentService(
        document_repository=document_repo,
        embedding_service=embedding_service,
        indexer_service=indexer_service,
    )

    # Orchestrator (recibe los servicios por inyección)
    orchestrator_service = OrchestratorService(document_service=document_service)

    app.state.orchestrator_service = orchestrator_service

    logger.info("Todos los servicios listos.")
    yield

    logger.info("Apagando GraphRAG…")
    neo4j.close()


app = FastAPI(
    title="GraphRAG API",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(orchestrator_router)


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}
