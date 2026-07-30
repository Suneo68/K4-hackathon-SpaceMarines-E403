import logging
import chromadb
from pathlib import Path
from config.settings import BASE_DIR, CHROMA_HOST, CHROMA_PORT, GEMINI_API_KEY, EMBEDDING_MODEL

from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from google import genai

logger = logging.getLogger(__name__)

# Tự định nghĩa (Custom) hàm Embedding dùng thư viện google-genai mới nhất
class ModernGeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            response = self.client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text
            )
            embeddings.append(response.embeddings[0].values)
        return embeddings

# Khởi tạo mô hình Embedding Đa ngôn ngữ (Gemini) để hiểu tiếng Việt
google_ef = ModernGeminiEmbeddingFunction(api_key=GEMINI_API_KEY)

# Initialize HTTP Client (Client-Server Mode for Production)
try:
    _chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    # Tạo collection mới (v2) để tránh xung đột chiều (dimension) với data cũ
    collection = _chroma_client.get_or_create_collection(
        name="kudo_knowledge_v2", 
        embedding_function=google_ef
    )
    logger.info(f"Connected to ChromaDB HTTP Server at {CHROMA_HOST}:{CHROMA_PORT} with Gemini Embedding")
except Exception as e:
    logger.error(f"Failed to connect to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}. Is the server running? Error: {e}")
    raise e


def upsert_documents(doc_ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
    """
    Upserts a batch of documents into the ChromaDB collection.
    Overwrites existing entries with the same doc_ids.
    """
    if not doc_ids:
        return
        
    try:
        collection.upsert(
            ids=doc_ids,
            documents=texts,
            metadatas=metadatas
        )
        logger.info(f"Upserted {len(doc_ids)} chunks into Vector DB.")
    except Exception as e:
        logger.error(f"Error upserting documents: {e}", exc_info=True)
        raise e


def delete_document(doc_id: str) -> None:
    """
    Delete a document (and all its chunks) from ChromaDB based on Discord message ID.
    Since chunks are named like 1234_part1, 1234_part2, we need to find and delete all of them.
    """
    if not doc_id:
        return

    try:
        # Tối ưu hóa: Dùng mệnh đề where để chỉ query đúng những chunk thuộc về message_id này
        results = collection.get(where={"message_id": str(doc_id)})
        ids_to_delete = results.get("ids", [])
        
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(f"Successfully deleted {len(ids_to_delete)} chunks for message ID '{doc_id}' from ChromaDB.")
        else:
            logger.warning(f"No chunks found for message ID '{doc_id}' to delete.")
    except Exception as e:
        logger.error(f"Failed to delete document ID '{doc_id}' from ChromaDB: {e}", exc_info=True)


def query_documents(query_text: str, top_k: int = 3) -> tuple[list[str], list[dict]]:
    """
    Search ChromaDB for the most relevant documents based on the query text.
    """
    if not query_text or not query_text.strip():
        return [], []

    try:
        results = collection.query(
            query_texts=[query_text.strip()],
            n_results=top_k
        )
        
        if not results or not results.get("documents") or not results["documents"][0]:
            return [], []

        documents = results["documents"][0]
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)

        return documents, metadatas
    except Exception as e:
        logger.error(f"Failed to query documents from ChromaDB: {e}", exc_info=True)
        return [], []
