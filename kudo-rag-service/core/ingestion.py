import re
import logging
from core.extractors import process_attachments, process_urls
from core.guardrails import sanitize_context_text
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Noise Filtering Patterns (Loại bỏ tin nhắn rác, chào hỏi, cám ơn lặt vặt)
GREETING_NOISE_PATTERNS = [
    r"^(dạ|ok|oki|okey|tks|thanks|cảm ơn|cam on|chào|helo|hello|dạ vâng|uy tín)\s*(\s*|ạ|thầy|mọi người|mng|ad|bot)*$",
    r"^(dạ|ok|cảm ơn|tks)\b"
]

def is_quality_knowledge_content(content: str, attachments: list = None) -> bool:
    """
    Noise Filter: Determines if a Discord message contains meaningful knowledge content.
    Rejects messages < 15 chars (without attachments/links) or greetings/acknowledgements.
    """
    if attachments:
        return True
        
    cleaned = content.strip().lower()
    
    # Keep if message contains a web URL
    if "http://" in cleaned or "https://" in cleaned:
        return True
        
    # Skip if too short (< 15 chars)
    if len(cleaned) < 15:
        logger.debug(f"Skipped noise message (Length < 15): '{content}'")
        return False
        
    # Skip if matches greeting/acknowledgement noise patterns
    for pattern in GREETING_NOISE_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            logger.info(f"🧹 Noise Filtered out greeting/acknowledgement message: '{content}'")
            return False
            
    return True

# Khởi tạo bộ chặt nhỏ văn bản
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,      # Tối đa 1200 ký tự mỗi đoạn
    chunk_overlap=200,    # Lặp lại 200 ký tự ở đuôi đoạn trước sang đầu đoạn sau (bảo toàn ngữ cảnh)
    length_function=len,
    is_separator_regex=False,
)

async def prepare_discord_message(
    message_id: str,
    content: str,
    attachments: list,
    channel_name: str,
    author: str,
    created_at: str,
    jump_url: str
) -> tuple[list[str], list[str], list[dict]]:
    """
    Extracts web text and attachment text, merges it, cleans indirect injections, and splits into small chunks.
    Returns: (list of chunk_ids, list of chunk_texts, list of metadata_dicts)
    """
    # 0. Noise Filtering (Lọc tin nhắn rác/xã giao)
    if not is_quality_knowledge_content(content, attachments):
        return [], [], []

    full_text = content.strip()
    
    # 1. Cào nội dung Website nếu trong tin nhắn có Link
    if full_text:
        web_text = await process_urls(full_text)
        if web_text:
            full_text += f"\n{web_text}"
            
    # 2. Đọc nội dung từ các file đính kèm
    if attachments:
        file_text = await process_attachments(attachments)
        if file_text:
            full_text += f"\n{file_text}"
            
    if len(full_text.strip()) < 5:
        logger.debug(f"Skipping message {message_id} because combined content length < 5.")
        return [], [], []

    # Sanitize context text against Indirect Prompt Injection (Data Poisoning)
    full_text = sanitize_context_text(full_text)


    # 3. Chặt nhỏ văn bản thành các Chunk (để nhét vừa vào Não AI)
    raw_chunks = text_splitter.split_text(full_text)
    
    chunk_ids = []
    formatted_chunks = []
    metadatas = []

    for i, chunk in enumerate(raw_chunks):
        # Đánh ID duy nhất cho từng mảnh vỡ (Ví dụ: 123456_part1)
        chunk_id = f"{message_id}_part{i+1}"
        
        # Gắn Header chỉ đường cho AI hiểu
        formatted_text = (
            f"[Nguồn: #{channel_name} | Người đăng: {author} | Thời gian: {created_at} | Phần {i+1}/{len(raw_chunks)}]\n"
            f"Nội dung: {chunk}"
        )
        
        metadata = {
            "message_id": str(message_id),
            "channel_name": str(channel_name),
            "author": str(author),
            "created_at": str(created_at),
            "jump_url": str(jump_url),
            "chunk_index": i + 1,
            "total_chunks": len(raw_chunks)
        }
        
        chunk_ids.append(chunk_id)
        formatted_chunks.append(formatted_text)
        metadatas.append(metadata)

    return chunk_ids, formatted_chunks, metadatas
