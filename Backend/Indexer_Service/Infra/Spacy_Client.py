import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class INERProvider(ABC):

    @abstractmethod
    def extract(self, text: str) -> list[tuple[str, str]]:
        """Retorna lista de (texto_entidad, tipo_entidad)."""
        ...


class SpacyNERProvider(INERProvider):

    def __init__(self, model_name: str = "es_core_news_sm"):
        try:
            import spacy
            self._nlp = spacy.load(model_name)
            logger.info("Modelo spaCy cargado: %s", model_name)
        except OSError:
            raise RuntimeError(
                f"Modelo spaCy '{model_name}' no encontrado. "
                f"Descárgalo con: python -m spacy download {model_name}"
            )
        except ImportError as exc:
            raise RuntimeError("Instala spaCy: pip install spacy") from exc

    def extract(self, text: str) -> list[tuple[str, str]]:
        doc = self._nlp(text)
        return [(ent.text.strip(), ent.label_) for ent in doc.ents if ent.text.strip()]