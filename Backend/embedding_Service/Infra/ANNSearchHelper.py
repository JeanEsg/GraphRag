from qdrant_client.models import SearchParams

class ANNSearchHelper:
    """
    Helper para aislar y explicitar la configuración de búsqueda aproximada (ANN) 
    utilizando el índice HNSW en Qdrant.
    """
    
    @staticmethod
    def get_hnsw_search_params(ef_search: int = 128, exact: bool = False) -> SearchParams:
        """
        Devuelve los parámetros de búsqueda configurando el comportamiento de HNSW.
        
        Args:
            ef_search: Controla el balance entre velocidad y precisión durante la búsqueda. 
                       Mayor ef_search = mayor precisión pero más lento.
            exact: Si es True, ignora el índice HNSW y hace una búsqueda exacta 
                   (fuerza bruta). Debe ser False para usar ANN.
        """
        return SearchParams(
            hnsw_ef=ef_search,
            exact=exact
        )
