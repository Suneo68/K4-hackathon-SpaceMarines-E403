import logging
from google import genai
from config import settings
from core.vector_store import query_documents

logger = logging.getLogger(__name__)

# Fallback response message adhering to HAX Rules G10 & G2
DEFAULT_FALLBACK = "Em chưa tìm thấy thông tin này trong các kênh thông báo/bài học, em đã ghi nhận để TA hỗ trợ nhé!"


def generate_rag_answer(user_query: str) -> tuple[str, list[str]]:
    """
    Generate an augmented answer for a user query using ChromaDB context and Google Gemini API.

    :param user_query: The question asked by the student/user.
    :return: A tuple of (answer_text, formatted_sources_list).
    """
    if not user_query or not user_query.strip():
        return DEFAULT_FALLBACK, []

    # 1. Retrieve top-3 relevant documents from ChromaDB
    documents, metadatas = query_documents(user_query.strip(), top_k=3)

    if not documents:
        logger.info(f"No context found in ChromaDB for query: '{user_query}'")
        return DEFAULT_FALLBACK, []

    # 2. Extract and format source citations
    formatted_sources: list[str] = []
    for meta in metadatas:
        channel = meta.get("channel_name", "kênh")
        author = meta.get("author", "N/A")
        jump_url = meta.get("jump_url", "")
        
        if jump_url:
            source_citation = f"#{channel} (đăng bởi {author}) - Link: {jump_url}"
        else:
            source_citation = f"#{channel} (đăng bởi {author})"

        if source_citation not in formatted_sources:
            formatted_sources.append(source_citation)

    # 3. Build System Prompt applying HAX Rules G10 & G2
    context_str = "\n\n---\n\n".join(documents)
    
    prompt = (
        "Bạn là trợ lý AI Discord cho cộng đồng khóa học AI20K (Kudo Assistant).\n"
        "Nhiệm vụ của bạn là trả lời câu hỏi của học viên dựa CHỈ VÀO các thông tin ngữ cảnh được cung cấp dưới đây.\n\n"
        "ÁP DỤNG CÁC QUY TẮC BẮT BUỘC (HAX Rules G10 & G2):\n"
        "1. Trả lời CHỈ dựa vào thông tin có trong phần 'NGỮ CẢNH TRI THỨC'. Tuyệt đối không tự suy đoán, bịa đặt hoặc sử dụng kiến thức ngoài ngữ cảnh này.\n"
        "2. Nếu phần ngữ cảnh KHÔNG chứa thông tin đủ để trả lời chính xác câu hỏi, bạn BẮT BUỘC phải trả lời chính xác câu sau:\n"
        f'"{DEFAULT_FALLBACK}"\n'
        "3. Giữ văn phong thân thiện, lịch sự và hỗ trợ học viên.\n\n"
        f"NGỮ CẢNH TRI THỨC:\n{context_str}\n\n"
        f"CÂU HỎI CỦA HỌC VIÊN:\n{user_query.strip()}"
    )

    # 4. Call Gemini API using gemini-2.5-flash
    try:
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not configured in settings.")
            return DEFAULT_FALLBACK, []

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt
        )

        answer_text = response.text.strip() if response and response.text else DEFAULT_FALLBACK
        
        # If model returned fallback text, return empty sources
        if DEFAULT_FALLBACK.lower() in answer_text.lower():
            return DEFAULT_FALLBACK, []

        return answer_text, formatted_sources

    except Exception as e:
        logger.error(f"Error invoking Gemini API in rag_chain: {e}", exc_info=True)
        return DEFAULT_FALLBACK, []
