import logging

logger = logging.getLogger(__name__)


def prepare_discord_message(
    content: str,
    channel_name: str,
    author: str,
    created_at: str,
    jump_url: str
) -> tuple[str, dict]:
    """
    Clean input message text and construct formatted text header with metadata.

    :param content: Raw text of the Discord message.
    :param channel_name: Name of the channel where message was posted.
    :param author: Author username or display name.
    :param created_at: Timestamp string when message was sent.
    :param jump_url: Direct URL link to the Discord message.
    :return: A tuple containing (formatted_document_string, metadata_dictionary).
             Returns ("", {}) if content after cleaning is shorter than 5 characters.
    """
    if not content:
        return "", {}

    cleaned_content = content.strip()
    if len(cleaned_content) < 5:
        logger.debug(f"Skipping message ingestion because content length ({len(cleaned_content)}) < 5.")
        return "", {}

    formatted_text = (
        f"[Nguồn: #{channel_name} | Người đăng: {author} | Thời gian: {created_at}]\n"
        f"Nội dung: {cleaned_content}"
    )

    metadata = {
        "channel_name": str(channel_name),
        "author": str(author),
        "created_at": str(created_at),
        "jump_url": str(jump_url)
    }

    return formatted_text, metadata
