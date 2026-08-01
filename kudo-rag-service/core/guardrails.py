import re
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

# List of patterns for Direct Prompt Injection detection
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above|system)\s+(instructions|rules|prompts|directives)",
    r"bỏ\s+qua\s+(mọi|tất\s+cả|các)\s+(quy\s+tắc|chỉ\s+dẫn|yêu\s+cầu|hướng\s+dẫn)",
    r"(show|print|reveal|display|output|tell\s+me)\s+(your|the)?\s*(system\s+prompt|initial\s+prompt|instructions)",
    r"in\s+ra\s+(toàn\s+bộ\s+)?(system\s+prompt|chỉ\s+dẫn\s+hệ\s+thống|prompt\s+ban\s+đầu|cấu\s+hình)",
    r"you\s+are\s+now\s+(dan|jailbroken|unrestricted|god\s+mode)",
    r"act\s+as\s+a\s+(jailbroken|unfiltered|unrestricted)",
    r"bypass\s+(hax|rules|g10|fallback)",
    r"quên\s+(đi|hết)\s+(tất\s+cả|các|mọi)\s+(chỉ\s+dẫn|quy\s+tắc)",
    r"bạn\s+là\s+dan\s+không\s+có\s+giới\s+hạn"
]

# Patterns for indirect prompt injection payloads inside documents/messages
INDIRECT_INJECTION_PATTERNS = [
    r"\[\s*system\s*(note|instruction|directive|rule|prompt)\s*:.*?\]",
    r"\[\s*ghi\s*chú\s*hệ\s*thống\s*:.*?\]",
    r"\[\s*lưu\s*ý\s*hệ\s*thống\s*:.*?\]",
    r"\[\s*ignore\s+context\s*:.*?\]"
]

SAFE_DOMAINS = [
    "github.com",
    "google.com",
    "drive.google.com",
    "docs.google.com",
    "discord.com",
    "discord.gg",
    "zalo.me",
    "youtube.com",
    "colab.research.google.com"
]


def validate_user_query(query: str) -> Tuple[bool, str]:
    """
    Input Guardrail: Validates user query against direct prompt injection attacks.
    Returns (is_safe, message_or_cleaned_query).
    """
    if not query or not query.strip():
        return True, query

    query_lower = query.lower().strip()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            logger.warning(f"🛡️ Guardrail Triggered! Direct Prompt Injection attempt blocked: '{query}'")
            refusal_msg = (
                "⚠️ **Cảnh báo An toàn**: Câu hỏi của bạn chứa các từ khóa thao túng hệ thống "
                "không được hỗ trợ bởi chính sách an toàn của Kudo Assistant. "
                "Vui lòng đặt lại câu hỏi liên quan đến kiến thức và nội dung khóa học!"
            )
            return False, refusal_msg

    return True, query.strip()


def sanitize_context_text(text: str) -> str:
    """
    Context Guardrail: Cleans extracted text from PDF/DOCX/OCR/Web URLs/Messages to remove indirect prompt injections.
    """
    if not text:
        return ""

    sanitized = text
    # 1. Remove bracketed system overrides like [system note: ...] or [ghi chú hệ thống: ...]
    for pattern in INDIRECT_INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)

    # 2. Remove adversarial injection phrases embedded in PDF, DOCX, Web URLs, or Image OCR
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, sanitized, re.IGNORECASE):
            logger.warning(f"🛡️ Context Guardrail: Neutralized prompt injection pattern in ingested text: '{pattern}'")
            sanitized = re.sub(pattern, "[Đã lọc câu lệnh không hợp lệ]", sanitized, flags=re.IGNORECASE)

    return sanitized.strip()


def sanitize_output_response(answer_text: str, context_sources: List[str]) -> str:
    """
    Output Guardrail: Sanitizes AI generated text, filtering unauthorized external URLs (Phishing Protection).
    """
    if not answer_text:
        return answer_text

    # Extract all URLs in answer text
    url_pattern = re.compile(r'https?://\S+')
    urls = url_pattern.findall(answer_text)

    if not urls:
        return answer_text

    context_str = " ".join(context_sources).lower()
    sanitized_answer = answer_text

    for url in urls:
        url_lower = url.lower()
        # Check if URL is present in context sources or belongs to SAFE_DOMAINS
        is_safe = any(domain in url_lower for domain in SAFE_DOMAINS) or (url_lower in context_str)

        if not is_safe:
            logger.warning(f"🛡️ Guardrail Triggered! Blocked unauthorized URL in AI answer: '{url}'")
            sanitized_answer = sanitized_answer.replace(url, "[Liên kết chưa xác thực đã bị ẩn để bảo mật]")

    return sanitized_answer


# --- PER-USER COOLDOWN RATE LIMITER ---
import time
import threading
from config import settings

_user_last_query_time = {}
_cooldown_lock = threading.Lock()

def check_user_cooldown(user_id: str, cooldown_seconds: int = None) -> Tuple[bool, float]:
    """
    Per-User Rate Limiter: Checks if a user is currently in cooldown period.
    Returns (is_allowed, remaining_seconds).
    """
    if not user_id:
        return True, 0.0

    if cooldown_seconds is None:
        cooldown_seconds = getattr(settings, 'USER_COOLDOWN_SECONDS', 2)

    now = time.time()
    user_key = str(user_id)
    
    with _cooldown_lock:
        if user_key in _user_last_query_time:
            elapsed = now - _user_last_query_time[user_key]
            if elapsed < cooldown_seconds:
                remaining = round(cooldown_seconds - elapsed, 1)
                return False, remaining

        _user_last_query_time[user_key] = now
        return True, 0.0

