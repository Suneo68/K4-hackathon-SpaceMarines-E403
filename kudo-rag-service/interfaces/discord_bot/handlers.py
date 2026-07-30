import logging
import discord
from config import settings
from core.ingestion import prepare_discord_message
from core.vector_store import upsert_document
from core.rag_chain import generate_rag_answer

logger = logging.getLogger(__name__)


def setup_bot_handlers(bot: discord.Client) -> None:
    """
    Register event handlers for the Discord bot instance.

    :param bot: The discord commands.Bot or Client instance.
    """

    @bot.event
    async def on_ready():
        logger.info(f"Bot logged in successfully as {bot.user} (ID: {bot.user.id})")
        print(f"✅ Bot is ready! Logged in as {bot.user} (ID: {bot.user.id})")

    @bot.event
    async def on_message(message: discord.Message):
        # Ignore messages sent by the bot itself or other bots
        if message.author.bot:
            return

        channel_name = getattr(message.channel, 'name', '').lower().strip()

        # Handle Forum Threads (Check parent channel's topic)
        channel_topic = getattr(message.channel, 'topic', '') or ''
        if hasattr(message.channel, 'parent') and message.channel.parent:
            parent_topic = getattr(message.channel.parent, 'topic', '') or ''
            channel_topic = f"{channel_topic} {parent_topic}"
        
        # Logic 1: Auto-Ingest messages from Knowledge Channels (Guarded by Topic Tag & Permissions)
        is_knowledge_channel = settings.KNOWLEDGE_TOPIC_TAG in channel_topic.upper()
        
        if is_knowledge_channel:
            # 1. Check if user has sufficient permissions (Manage Channels or Administrator)
            is_authorized = False
            if hasattr(message.author, 'guild_permissions'):
                perms = message.author.guild_permissions
                is_authorized = getattr(perms, 'administrator', False) or getattr(perms, 'manage_channels', False)
            
            if not is_authorized:
                logger.debug(f"Ignored ingestion: Message from {message.author} in #{channel_name} (Insufficient permissions)")
            else:
                try:
                    formatted_text, metadata = prepare_discord_message(
                        content=message.content,
                        channel_name=getattr(message.channel, 'name', 'unknown'),
                        author=str(message.author.display_name or message.author.name),
                        created_at=message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        jump_url=message.jump_url
                    )

                    if formatted_text:
                        upsert_document(
                            doc_id=str(message.id),
                            text=formatted_text,
                            metadata=metadata
                        )
                        logger.info(f"Successfully auto-ingested message ID {message.id} from #{channel_name} (Author: {message.author})")
                except Exception as e:
                    logger.error(f"Error during auto-ingestion for message {message.id}: {e}", exc_info=True)

        # Logic 2: QA RAG Response ONLY when @Mentioned
        is_mentioned = False
        if bot.user:
            is_mentioned = any(u.id == bot.user.id for u in message.mentions)

        if is_mentioned:
            try:
                async with message.channel.typing():
                    # Clean bot mention from content string
                    user_query = message.content
                    if bot.user:
                        user_query = user_query.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "")
                    user_query = user_query.strip()

                    if user_query:
                        answer, sources = generate_rag_answer(user_query)

                        reply_text = answer
                        if sources:
                            reply_text += "\n\n📌 **Nguồn tham khảo:**\n" + "\n".join([f"• {src}" for src in sources])

                        await message.reply(reply_text, mention_author=True)
            except Exception as e:
                logger.error(f"Error processing QA message {message.id}: {e}", exc_info=True)
                await message.reply("⚠️ Có lỗi xảy ra khi xử lý câu hỏi của bạn. Vui lòng thử lại sau!", mention_author=True)

        # Process any command decorators registered on the bot
        await bot.process_commands(message)
