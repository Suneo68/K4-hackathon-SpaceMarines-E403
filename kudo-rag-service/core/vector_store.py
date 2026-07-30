import logging
import chromadb
from pathlib import Path
from config.settings import BASE_DIR

logger = logging.getLogger(__name__)

# Directory path for ChromaDB storage
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Initialize Persistent Client
_chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

# Get or create collection for Kudo RAG knowledge
collection = _chroma_client.get_or_create_collection(name="kudo_knowledge")


def upsert_document(doc_id: str, text: str, metadata: dict) -> None:
    """
    Save or update a text document and its associated metadata in ChromaDB.

    :param doc_id: Unique identifier for the document (e.g., Discord message ID).
    :param text: Cleaned and formatted text content to embed.
    :param metadata: Metadata dictionary (channel_name, author, created_at, jump_url).
    """
    if not doc_id or not text or not text.strip():
        logger.warning("Attempted to upsert empty doc_id or text into ChromaDB.")
        return

    try:
        collection.upsert(
            ids=[str(doc_id)],
            documents=[text.strip()],
            metadatas=[metadata]
        )
        logger.info(f"Successfully upserted document ID '{doc_id}' into ChromaDB.")
    except Exception as e:
        logger.error(f"Failed to upsert document ID '{doc_id}' to ChromaDB: {e}", exc_info=True)
        raise e


def query_documents(query_text: str, top_k: int = 3) -> tuple[list[str], list[dict]]:
    """
    Query ChromaDB for top_k most relevant documents based on semantic similarity.

    :param query_text: User question or query text.
    :param top_k: Number of relevant documents to retrieve.
    :return: A tuple containing (list of document texts, list of metadata dicts).
    """
    if not query_text or not query_text.strip():
        return [], []

    try:
        count = collection.count()
        if count == 0:
            logger.info("ChromaDB collection is empty.")
            return [], []

        # Ensure n_results does not exceed total documents available
        n_results = min(top_k, count)

        results = collection.query(
            query_texts=[query_text.strip()],
            n_results=n_results
        )

        documents = results.get("documents", [[]])[0] if results.get("documents") else []
        metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

        return documents, metadatas
    except Exception as e:
        logger.error(f"Error querying ChromaDB with text '{query_text}': {e}", exc_info=True)
        return [], []
