import json
import logging
import time
import asyncio
from google import genai
from config import settings
from core.vector_store import query_documents
from core.experts_db import get_all_tags
from core.guardrails import validate_user_query, sanitize_output_response

logger = logging.getLogger(__name__)

# Fallback response message adhering to HAX Rules G10 & G2
DEFAULT_FALLBACK = "Em chưa tìm thấy thông tin này trong các kênh thông báo/bài học, em đã ghi nhận để TA hỗ trợ nhé!"


OFFICIAL_CHANNEL_KEYWORDS = [
    "thông-báo", "thong-bao",
    "tài-nguyên", "tai-nguyen",
    "rules", "quy-tắc", "quy-tac",
    "bài-học", "bai-hoc",
    "thực-hành-lab", "thuc-hanh-lab", "lab",
    "announcements", "resources", "knowledge"
]


def sort_and_tag_documents_by_recency(documents: list[str], metadatas: list[dict]) -> tuple[list[str], list[dict]]:
    """
    Channel Authority & Recency Relevance Ranking:
    Sorts retrieved document chunks prioritizing official channels (#thong-bao, #tai-nguyen, #giao-trinh)
    and newer creation timestamps. Adds authority tags to top chunks.
    """
    if not documents:
        return [], []

    paired = list(zip(documents, metadatas))
    
    def ranking_key(item: tuple) -> tuple:
        doc, meta = item
        channel = str(meta.get("channel_name", "")).lower()
        created_at = str(meta.get("created_at", ""))
        
        # Check if chunk originates from an official channel
        is_official = any(kw in channel for kw in OFFICIAL_CHANNEL_KEYWORDS)
        
        # Sort key: (is_official: True > False, created_at: Newest > Oldest)
        return (1 if is_official else 0, created_at)

    # Sort paired list descending by (official_priority, created_at)
    paired.sort(key=ranking_key, reverse=True)

    sorted_docs = []
    sorted_metas = []

    for i, (doc, meta) in enumerate(paired):
        channel = str(meta.get("channel_name", "")).lower()
        is_official = any(kw in channel for kw in OFFICIAL_CHANNEL_KEYWORDS)
        
        if i == 0 and is_official:
            doc_tagged = f"[⭐ NGUỒN CHÍNH THỨC - CẬP NHẬT MỚI NHẤT]\n{doc}"
        elif is_official:
            doc_tagged = f"[⭐ NGUỒN CHÍNH THỨC]\n{doc}"
        elif i == 0:
            doc_tagged = f"[📌 CẬP NHẬT MỚI NHẤT]\n{doc}"
        else:
            doc_tagged = doc
            
        sorted_docs.append(doc_tagged)
        sorted_metas.append(meta)

    return sorted_docs, sorted_metas


# --- EXPONENTIAL BACKOFF RETRY LOGIC (FOR 429 & 503 ERRORS) ---
def _call_gemini_with_retry(client, model: str, contents, max_retries: int = None):
    """
    Calls Gemini API with exponential backoff retry for 429 Rate Limits or 503 temporary errors.
    """
    if max_retries is None:
        max_retries = getattr(settings, 'MAX_LLM_RETRIES', 3)
    
    backoff = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents
            )
            return response
        except Exception as e:
            err_str = str(e).lower()
            if ("429" in err_str or "resourceexhausted" in err_str or "503" in err_str or "unavailable" in err_str) and attempt < max_retries:
                logger.warning(f"Gemini API Rate Limit / Temporary Error (Attempt {attempt}/{max_retries}): {e}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2.0
            else:
                raise e


# --- CONCURRENCY SEMAPHORE ---

_rag_semaphore = None

def _get_rag_semaphore():
    global _rag_semaphore
    if _rag_semaphore is None:
        max_concurrent = getattr(settings, 'MAX_CONCURRENT_RAG', 5)
        _rag_semaphore = asyncio.Semaphore(max_concurrent)
    return _rag_semaphore

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
        response = _call_gemini_with_retry(
            client=client,
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
        response = _call_gemini_with_retry(
            client=client,
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
        response = _call_gemini_with_retry(
            client=client,
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

    # 0. Input Guardrail (Chống Direct Prompt Injection)
    is_safe, check_res = validate_user_query(user_query)
    if not is_safe:
        return check_res, []

    # 1. Retrieve top-K relevant documents from ChromaDB
    documents, metadatas = query_documents(user_query.strip(), top_k=settings.TOP_K_RESULTS)

    if not documents:
        logger.info(f"No context found in ChromaDB for query: '{user_query}'")
        return DEFAULT_FALLBACK, []

    # Recency Relevance Ranking (Sắp xếp ưu tiên thông báo mới nhất)
    documents, metadatas = sort_and_tag_documents_by_recency(documents, metadatas)

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
    
    current_time_gmt7 = settings.get_current_gmt7_str()
    prompt = (
        "Bạn là trợ lý AI Discord cho cộng đồng khóa học AI20K (Kudo Assistant).\n"
        f"THỜI GIAN HIỆN TẠI KHI HỌC VIÊN HỎI: {current_time_gmt7}\n\n"
        "Nhiệm vụ của bạn là trả lời câu hỏi của học viên dựa CHỈ VÀO các thông tin ngữ cảnh được cung cấp dưới đây.\n"
        "LƯU Ý VỀ THỜI GIAN & MÔN HỌC/CẬP NHẬT/TRỌNG SỐ KÊNH:\n"
        "1. Nếu học viên sử dụng các từ chỉ thời gian tương đối như 'nay', 'hôm nay', 'ngày mai', 'hôm qua', 'tuần này', hãy đối chiếu từ đó với 'THỜI GIAN HIỆN TẠI KHI HỌC VIÊN HỎI' ở trên và mốc 'Thời gian' trong phần NGỮ CẢNH TRI THỨC.\n"
        "2. Các đoạn ngữ cảnh đã được xếp theo ưu tiên Trọng số Kênh (Chính thức) và Thứ tự thời gian từ MỚI NHẤT đến CŨ HƠN. Nếu có sự mâu thuẫn hoặc thay đổi giữa các thông báo (ví dụ: gia hạn deadline, thay đổi phòng học, cập nhật bài tập), bạn BẮT BUỘC phải ƯU TIÊN thông tin từ các kênh chính thống (#thong-bao, #tai-nguyen, #giao-trinh, #bai-hoc) và mốc thời gian MỚI NHẤT.\n\n"
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
        response = _call_gemini_with_retry(
            client=client,
            model=settings.LLM_MODEL,
            contents=prompt
        )

        answer_text = response.text.strip() if response and response.text else DEFAULT_FALLBACK
        
        # If model returned fallback text, return empty sources
        if DEFAULT_FALLBACK.lower() in answer_text.lower():
            return DEFAULT_FALLBACK, []

        # Output Guardrail (Chống Link Lừa đảo / Phishing)
        answer_text = sanitize_output_response(answer_text, formatted_sources)

        return answer_text, formatted_sources

    except Exception as e:
        logger.error(f"Error invoking Gemini API in rag_chain: {e}", exc_info=True)
        return DEFAULT_FALLBACK, []


def generate_rag_answer_with_trace(user_query: str) -> dict:
    """
    Executes RAG pipeline with high-precision latency, token metrics, and diagnostic tracing.
    """
    import time
    start_total = time.perf_counter()
    metrics = {
        "user_query": user_query,
        "retrieval_time_s": 0.0,
        "llm_time_s": 0.0,
        "total_time_s": 0.0,
        "retrieved_chunks_count": 0,
        "prompt_tokens": 0,
        "candidate_tokens": 0,
        "total_tokens": 0,
        "answer": DEFAULT_FALLBACK,
        "sources": [],
        "decision": "FALLBACK_NO_CONTEXT",
        "expert_tag": None
    }

    if not user_query or not user_query.strip():
        metrics["total_time_s"] = round(time.perf_counter() - start_total, 4)
        return metrics

    # 0. Input Guardrail
    is_safe, check_res = validate_user_query(user_query)
    if not is_safe:
        metrics["answer"] = check_res
        metrics["decision"] = "BLOCKED_BY_GUARDRAIL"
        metrics["total_time_s"] = round(time.perf_counter() - start_total, 4)
        return metrics

    # 1. Retrieve from ChromaDB with latency timing
    t0_retrieval = time.perf_counter()
    documents, metadatas = query_documents(user_query.strip(), top_k=settings.TOP_K_RESULTS)
    metrics["retrieval_time_s"] = round(time.perf_counter() - t0_retrieval, 4)
    metrics["retrieved_chunks_count"] = len(documents)

    if not documents:
        metrics["total_time_s"] = round(time.perf_counter() - start_total, 4)
        return metrics

    # Recency Relevance Ranking
    documents, metadatas = sort_and_tag_documents_by_recency(documents, metadatas)

    # Extract sources
    formatted_sources: list[str] = []
    for meta in metadatas:
        channel = meta.get("channel_name", "kênh")
        author = meta.get("author", "N/A")
        jump_url = meta.get("jump_url", "")
        source_citation = f"#{channel} (đăng bởi {author}) - Link: {jump_url}" if jump_url else f"#{channel} (đăng bởi {author})"
        if source_citation not in formatted_sources:
            formatted_sources.append(source_citation)

    context_str = "\n\n---\n\n".join(documents)
    current_time_gmt7 = settings.get_current_gmt7_str()
    prompt = (
        "Bạn là trợ lý AI Discord cho cộng đồng khóa học AI20K (Kudo Assistant).\n"
        f"THỜI GIAN HIỆN TẠI KHI HỌC VIÊN HỎI: {current_time_gmt7}\n\n"
        "Nhiệm vụ của bạn là trả lời câu hỏi của học viên dựa CHỈ VÀO các thông tin ngữ cảnh được cung cấp dưới đây.\n"
        "LƯU Ý VỀ THỜI GIAN & MÔN HỌC/CẬP NHẬT/TRỌNG SỐ KÊNH:\n"
        "1. Nếu học viên sử dụng các từ chỉ thời gian tương đối như 'nay', 'hôm nay', 'ngày mai', 'hôm qua', 'tuần này', hãy đối chiếu từ đó với 'THỜI GIAN HIỆN TẠI KHI HỌC VIÊN HỎI' ở trên và mốc 'Thời gian' trong phần NGỮ CẢNH TRI THỨC.\n"
        "2. Các đoạn ngữ cảnh đã được xếp theo ưu tiên Trọng số Kênh (Chính thức) và Thứ tự thời gian từ MỚI NHẤT đến CŨ HƠN. Nếu có sự mâu thuẫn hoặc thay đổi giữa các thông báo (ví dụ: gia hạn deadline, thay đổi phòng học, cập nhật bài tập), bạn BẮT BUỘC phải ƯU TIÊN thông tin từ các kênh chính thống (#thong-bao, #tai-nguyen, #giao-trinh, #bai-hoc) và mốc thời gian MỚI NHẤT.\n\n"
        "ÁP DỤNG CÁC QUY TẮC BẮT BUỘC (HAX Rules G10 & G2):\n"
        "1. Trả lời CHỈ dựa vào thông tin có trong phần 'NGỮ CẢNH TRI THỨC'. Tuyệt đối không tự suy đoán, bịa đặt hoặc sử dụng kiến thức ngoài ngữ cảnh này.\n"
        "2. Nếu phần ngữ cảnh KHÔNG chứa thông tin đủ để trả lời chính xác câu hỏi, bạn BẮT BUỘC phải trả lời chính xác câu sau:\n"
        f'"{DEFAULT_FALLBACK}"\n'
        "3. Giữ văn phong thân thiện, lịch sự và hỗ trợ học viên.\n\n"
        f"NGỮ CẢNH TRI THỨC:\n{context_str}\n\n"
        f"CÂU HỎI CỦA HỌC VIÊN:\n{user_query.strip()}"
    )

    # 2. Invoke Gemini LLM with latency and token usage tracking
    t0_llm = time.perf_counter()
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = _call_gemini_with_retry(
            client=client,
            model=settings.LLM_MODEL,
            contents=prompt
        )
        metrics["llm_time_s"] = round(time.perf_counter() - t0_llm, 4)

        if response and hasattr(response, 'usage_metadata') and response.usage_metadata:
            metrics["prompt_tokens"] = getattr(response.usage_metadata, 'prompt_token_count', 0) or 0
            metrics["candidate_tokens"] = getattr(response.usage_metadata, 'candidates_token_count', 0) or 0
            metrics["total_tokens"] = getattr(response.usage_metadata, 'total_token_count', 0) or 0

        answer_text = response.text.strip() if response and response.text else DEFAULT_FALLBACK

        if DEFAULT_FALLBACK.lower() in answer_text.lower():
            metrics["answer"] = DEFAULT_FALLBACK
            metrics["sources"] = []
            metrics["decision"] = "FALLBACK_INSUFFICIENT_CONTEXT"
            metrics["expert_tag"] = route_to_expert(user_query)
        else:
            # Output Guardrail
            answer_text = sanitize_output_response(answer_text, formatted_sources)
            metrics["answer"] = answer_text
            metrics["sources"] = formatted_sources
            metrics["decision"] = "SUCCESS_GROUNDED_RAG"

    except Exception as e:
        logger.error(f"Error in generate_rag_answer_with_trace: {e}", exc_info=True)
        metrics["answer"] = DEFAULT_FALLBACK
        metrics["decision"] = f"ERROR ({e})"

    metrics["total_time_s"] = round(time.perf_counter() - start_total, 4)
    return metrics


# --- ASYNC NON-BLOCKING WRAPPERS (TO PREVENT EVENT LOOP FREEZING) ---
import asyncio

async def async_route_to_expert(user_query: str) -> str:
    """Async non-blocking wrapper for route_to_expert"""
    return await asyncio.to_thread(route_to_expert, user_query)

async def async_summarize_text(text: str) -> str:
    """Async non-blocking wrapper for summarize_text"""
    return await asyncio.to_thread(summarize_text, text)

async def async_synthesize_thread_answers(old_contents: list[str], new_answer: str) -> str:
    """Async non-blocking wrapper for synthesize_thread_answers"""
    return await asyncio.to_thread(synthesize_thread_answers, old_contents, new_answer)

async def async_generate_rag_answer(user_query: str) -> tuple[str, list[str]]:
    """Async non-blocking wrapper for generate_rag_answer with Semaphore Limiter (Real-time, No Cache)"""
    sem = _get_rag_semaphore()
    async with sem:
        return await asyncio.to_thread(generate_rag_answer, user_query)

async def async_generate_rag_answer_with_trace(user_query: str) -> dict:
    """Async non-blocking wrapper for generate_rag_answer_with_trace with Semaphore Limiter"""
    sem = _get_rag_semaphore()
    async with sem:
        return await asyncio.to_thread(generate_rag_answer_with_trace, user_query)


