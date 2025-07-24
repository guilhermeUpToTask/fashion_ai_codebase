import chromadb
from threading import Lock

class ChromaClientWrapper:
    def __init__(self, host="chroma_db", port=8000):
        self.host = host
        self.port = port
        self._client = None
        self._lock = Lock()

    def get_client(self):
        # thread-safe lazy init
        if self._client is None:
            with self._lock:
                if self._client is None:
                    try:
                        self._client = chromadb.HttpClient(host=self.host, port=self.port)
                    except Exception as e:
                        # Log, mas não trave a aplicação
                        print(f"[ChromaClient] Error connecting: {e}")
                        # Pode decidir se quer lançar erro ou deixar None
                        raise
        return self._client


# Cria o wrapper global
chroma_client_wrapper = ChromaClientWrapper()

# Usa isso dentro do task:
# client = chroma_client_wrapper.get_client()
