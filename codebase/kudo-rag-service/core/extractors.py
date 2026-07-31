import re
import io
import os
import time
import tempfile
import logging
import asyncio
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import docx
from PIL import Image
from google import genai
from config.settings import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Initialize GenAI Client once at module level for connection pooling
_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def _describe_image(img_path: str) -> str:
    """Helper function to resize and describe image using Gemini API with retry logic."""
    if not _client:
        logger.error("GEMINI_API_KEY is missing. Cannot perform image OCR.")
        return ""

    try:
        # 1. Resize image if too large (Throttling / Performance optimization)
        img = Image.open(img_path)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        img.thumbnail((1024, 1024)) # Giữ nguyên tỷ lệ, giới hạn max 1024x1024
        
        # 2. Structured OCR Prompt for accurate RAG Retrieval
        prompt = (
            "Hãy đọc và trích xuất TOÀN BỘ chữ có trong bức ảnh này một cách chính xác nhất.\n"
            "- Giữ nguyên các mốc thời gian, ngày tháng, hạn chót (deadline), con số và tiêu đề.\n"
            "- Nếu là thông báo, biểu đồ hoặc sơ đồ, hãy diễn giải đầy đủ các ý chính, yêu cầu và lưu ý chi tiết."
        )
        
        # 3. Call Gemini API with automatic retries for temporary 503 errors
        for attempt in range(3):
            try:
                response = _client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[img, prompt]
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini Vision API attempt {attempt + 1}/3 failed ({e}). Retrying in 2 seconds...")
                time.sleep(2)
                
        return ""
    except Exception as e:
        logger.error(f"Error extracting image text: {e}", exc_info=True)
        return ""



async def process_attachments(attachments) -> str:
    """
    Downloads and extracts text from Discord attachments (PDF, DOCX, TXT, MD).
    Optimized for RAM by saving to temp files and setting a 20MB limit.
    Returns a combined string of all extracted texts.
    """
    extracted_text = ""
    MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB Giới hạn chống tràn RAM

    for attachment in attachments:
        if attachment.size > MAX_SIZE_BYTES:
            logger.warning(f"Bỏ qua file {attachment.filename} vì quá nặng ({attachment.size/1024/1024:.2f} MB).")
            continue

        filename = attachment.filename.lower()
        temp_path = None
        
        try:
            # 1. Tạo file tạm trên ổ cứng (Temp File)
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_path = temp_file.name

            # 2. Discord tự động tải và stream thẳng xuống ổ cứng (Không nạp hết vào RAM)
            await attachment.save(temp_path)

            if filename.endswith(".pdf"):
                # PyMuPDF đọc từng trang từ ổ cứng
                pdf_doc = fitz.open(temp_path)
                text = ""
                for page in pdf_doc:
                    text += page.get_text()
                pdf_doc.close()
                extracted_text += f"\n\n--- 📄 NỘI DUNG FILE: {attachment.filename} ---\n{text}\n"
                
            elif filename.endswith(".docx"):
                doc = docx.Document(temp_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                extracted_text += f"\n\n--- 📄 NỘI DUNG FILE: {attachment.filename} ---\n{text}\n"
                
            elif filename.endswith((".txt", ".md", ".csv", ".json")):
                with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                extracted_text += f"\n\n--- 📄 NỘI DUNG FILE: {attachment.filename} ---\n{text}\n"
                
            elif filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
                # Chạy ngầm việc gọi API Gemini để không block Bot
                img_text = await asyncio.to_thread(_describe_image, temp_path)
                if img_text:
                    extracted_text += f"\n\n--- 🖼️ MÔ TẢ HÌNH ẢNH: {attachment.filename} ---\n{img_text}\n"
                
        except Exception as e:
            logger.error(f"Error parsing attachment {filename}: {e}", exc_info=True)
        finally:
            # 3. Dọn dẹp rác (Xóa file tạm) dù có lỗi hay không
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            
    return extracted_text

def extract_urls(text: str) -> list:
    """Finds all URLs in a text string."""
    url_pattern = re.compile(r'https?://\S+')
    return url_pattern.findall(text)

async def process_urls(text: str) -> str:
    """
    Extracts URLs from text, fetches them, and parses HTML into clean text.
    Uses asyncio.to_thread to avoid blocking the Discord bot.
    """
    urls = extract_urls(text)
    if not urls:
        return ""
        
    extracted_text = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for url in urls:
        try:
            # Chạy requests.get trong thread riêng để không làm đơ (block) Bot
            response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Xóa các thẻ rác (code script, CSS, quảng cáo, header/footer)
                for script in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    script.extract()
                    
                page_text = soup.get_text(separator=' ', strip=True)
                # Giới hạn dung lượng text cào được (tránh tràn RAM nếu trang quá lớn)
                if len(page_text) > 20000:
                    page_text = page_text[:20000] + "\n...[Đã cắt bớt do quá dài]"
                    
                extracted_text += f"\n\n--- 🌐 NỘI DUNG WEBSITE: {url} ---\n{page_text}\n"
        except Exception as e:
            logger.warning(f"Error scraping URL {url}: {e}")
            
    return extracted_text
