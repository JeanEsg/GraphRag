import logging
from neo4j import Driver

logger = logging.getLogger(__name__)


class GraphRepository:

    def __init__(self, driver: Driver):
        self._driver = driver
        self._create_constraints()

    def _create_constraints(self) -> None:
        """
        Define constraints e índices al arrancar.
        Equivalente a las 'colecciones' en Qdrant.
        """
        with self._driver.session() as session:
            # Unicidad de documentos
            session.run("""
                CREATE CONSTRAINT document_id_unique IF NOT EXISTS
                FOR (d:Document) REQUIRE d.document_id IS UNIQUE
            """)
            # Unicidad de chunks
            session.run("""
                CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
                FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE
            """)
            # Índice de entidades para búsqueda rápida
            session.run("""
                CREATE INDEX entity_text_index IF NOT EXISTS
                FOR (e:Entity) ON (e.text)
            """)
            logger.info("Constraints e índices de Neo4j verificados")

    def upsert_document(self, document_id: str, filename: str) -> None:
        with self._driver.session() as session:
            session.run("""
                MERGE (d:Document {document_id: $document_id})
                SET d.filename = $filename
            """, document_id=document_id, filename=filename)

    def upsert_chunk(
        self,
        document_id: str,
        chunk_id: str,
        chunk_index: int,
        text: str,
    ) -> None:
        with self._driver.session() as session:
            # Crear chunk y relacionarlo con el documento
            session.run("""
                MERGE (c:Chunk {chunk_id: $chunk_id})
                SET c.text = $text,
                    c.chunk_index = $chunk_index,
                    c.document_id = $document_id
                WITH c
                MATCH (d:Document {document_id: $document_id})
                MERGE (d)-[:HAS_CHUNK]->(c)
            """, chunk_id=chunk_id, text=text,
                chunk_index=chunk_index, document_id=document_id)

    def link_consecutive_chunks(
        self,
        chunk_id_current: str,
        chunk_id_next: str,
    ) -> None:
        with self._driver.session() as session:
            session.run("""
                MATCH (a:Chunk {chunk_id: $current})
                MATCH (b:Chunk {chunk_id: $next})
                MERGE (a)-[:NEXT_CHUNK]->(b)
            """, current=chunk_id_current, next=chunk_id_next)

    def upsert_entity_and_link(
        self,
        chunk_id: str,
        entity_text: str,
        entity_label: str,
    ) -> None:
        with self._driver.session() as session:
            session.run("""
                MERGE (e:Entity {text: $text, label: $label})
                WITH e
                MATCH (c:Chunk {chunk_id: $chunk_id})
                MERGE (c)-[:MENTIONS]->(e)
            """, text=entity_text, label=entity_label, chunk_id=chunk_id)


    def search_chunks_by_entities(self, entities: list[str], limit: int = 15) -> list[dict]:
        """
        Realiza una búsqueda exploratoria en el grafo:
        1. Chunks que mencionan las entidades directamente.
        2. Chunks vecinos (anterior/siguiente) para mantener el contexto.
        3. Chunks de otras entidades que co-ocurren con las buscadas.
        """
        if not entities:
            return []
            
        with self._driver.session() as session:
            # Esta query es el "motor de exploración":
            # Encuentra la entidad -> sus chunks -> vecinos -> otras entidades en esos chunks -> sus chunks.
            result = session.run("""
                MATCH (e:Entity)
                WHERE toLower(e.text) IN [ent IN $entities | toLower(ent)]
                
                // Nivel 1: Chunks directos y sus vecinos inmediatos
                MATCH (e)<-[:MENTIONS]-(c:Chunk)
                OPTIONAL MATCH (c)-[:NEXT_CHUNK*0..1]-(neighbor:Chunk)
                
                // Nivel 2: Co-ocurrencia (Otras entidades en los mismos chunks)
                OPTIONAL MATCH (neighbor)-[:MENTIONS]->(co_entity:Entity)<-[:MENTIONS]-(co_chunk:Chunk)
                
                WITH neighbor, co_chunk, e
                UNWIND [neighbor, co_chunk] AS result_chunk
                
                RETURN DISTINCT result_chunk.chunk_id AS chunk_id, 
                       result_chunk.text AS text, 
                       result_chunk.document_id AS document_id, 
                       e.text AS matched_entity
                LIMIT $limit
            """, entities=entities, limit=limit)
            return [record.data() for record in result]


