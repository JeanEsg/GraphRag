import logging
import os

from Config import settings

logger = logging.getLogger(__name__)


class DocumentRepository:

    def __init__(self):
        os.makedirs(settings.upload_dir, exist_ok=True)

    async def save_file(self, filename: str, file_content: bytes, document_id: str) -> str:
        """
        Guarda el archivo en el directorio de uploads.
        Usa document_id como prefijo para evitar colisiones de nombre.
        Retorna la ruta absoluta del archivo guardado.
        """
        stored_filename = f"{document_id}_{filename}"
        file_path = os.path.join(settings.upload_dir, stored_filename)

        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info("Archivo guardado en: %s", file_path)
        return file_path
