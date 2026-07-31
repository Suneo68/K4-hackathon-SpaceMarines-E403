import logging
from core.extractors import process_attachments, process_urls
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

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
    Extracts web text and attachment text, merges it, and splits into small chunks.
    Returns: (list of chunk_ids, list of chunk_texts, list of metadata_dicts)
    """
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
