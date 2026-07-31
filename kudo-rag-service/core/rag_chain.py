import json
import logging
from google import genai
from config import settings
from core.vector_store import query_documents
from core.experts_db import get_all_tags

logger = logging.getLogger(__name__)

# Fallback response message adhering to HAX Rules G10 & G2
DEFAULT_FALLBACK = "Em chưa tìm thấy thông tin này trong các kênh thông báo/bài học, em đã ghi nhận để TA hỗ trợ nhé!"

def route_to_expert(user_query: str) -> str:
    """Returns the best matching tag or None based on user query"""
    tags = get_all_tags()
    if not tags:
        return None
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = (
        "Bạn là một hệ thống phân luồng (Router). "
        "Dưới đây là danh sách các lĩnh vực chuyên môn hiện có: "
        f"{json.dumps(tags, ensure_ascii=False)}\n\n"
        f"Câu hỏi của người dùng: '{user_query}'\n\n"
        "Hãy chọn 1 lĩnh vực phù hợp nhất từ danh sách trên để người dùng có thể hỏi chuyên gia. "
        "Nếu không có lĩnh vực nào phù hợp, hãy trả về 'NONE'. "
        "Chỉ trả về ĐÚNG TÊN LĨNH VỰC hoặc 'NONE', KHÔNG giải thích gì thêm."
    )
    
    try:
        response = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
        )
        result = response.text.strip().lower()
        if result in tags:
            return result
        return None
    except Exception as e:
        logger.error(f"Error in route_to_expert: {e}")
        return None


def summarize_text(text: str) -> str:
    """
    Summarize a given block of text using Gemini.
    """
    if not text.strip():
        return "Không có nội dung nào để tóm tắt."
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = (
        "Bạn là một trợ giảng AI mẫn cán. "
        "Hãy đọc các tin nhắn/thông báo sau đây và viết một bản tóm tắt thật ngắn gọn, súc tích, "
        "nhấn mạnh vào các sự kiện, hạn chót (deadline) hoặc tài liệu quan trọng.\n\n"
        f"Nội dung cần tóm tắt:\n{text}"
    )
    
    try:
        response = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Error during summarization: {e}")
        return "Xin lỗi, em đang gặp chút sự cố khi tóm tắt thông tin."

def synthesize_thread_answers(old_contents: list[str], new_answer: str) -> str:
    """
    Combine previous answers and a new answer into one cohesive solution using LLM.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    old_text = "\n---\n".join(old_contents)
    prompt = (
        "Bạn là một chuyên gia tổng hợp kiến thức. Dưới đây là các giải pháp cũ đã được lưu trữ cho một vấn đề, "
        "và một giải pháp MỚI vừa được thêm vào.\n\n"
        f"Các giải pháp cũ:\n{old_text}\n\n"
        f"Giải pháp MỚI:\n{new_answer}\n\n"
        "Nhiệm vụ: Hãy gộp tất cả các giải pháp này lại thành MỘT bài hướng dẫn/giải pháp hoàn chỉnh, mạch lạc, súc tích. "
        "Loại bỏ các ý trùng lặp, giữ lại tất cả các góc nhìn đúng. Trình bày rõ ràng dễ hiểu."
    )
    
    try:
        response = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Error during synthesis: {e}")
        return new_answer


def generate_rag_answer(user_query: str) -> tuple[str, list[str]]:
    """
    Generate an augmented answer for a user query using ChromaDB context and Google Gemini API.

    :param user_query: The question asked by the student/user.
    :return: A tuple of (answer_text, formatted_sources_list).
    """
    if not user_query or not user_query.strip():
        return DEFAULT_FALLBACK, []

    # 1. Retrieve top-K relevant documents from ChromaDB
    documents, metadatas = query_documents(user_query.strip(), top_k=settings.TOP_K_RESULTS)

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
