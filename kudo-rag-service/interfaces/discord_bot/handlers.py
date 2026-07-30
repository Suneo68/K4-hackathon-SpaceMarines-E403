import logging
import discord
from discord import app_commands
from discord.ext import commands
from config import settings
from core.ingestion import prepare_discord_message
from core.vector_store import upsert_documents, delete_document
from core.rag_chain import generate_rag_answer, summarize_text, route_to_expert, DEFAULT_FALLBACK
from core import experts_db

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
        try:
            if settings.SANDBOX_GUILD_ID:
                guild = discord.Object(id=int(settings.SANDBOX_GUILD_ID))
                bot.tree.copy_global_to(guild=guild)
                synced = await bot.tree.sync(guild=guild)
                print(f"✅ Synced {len(synced)} slash command(s) to guild {settings.SANDBOX_GUILD_ID}")
            else:
                synced = await bot.tree.sync()
                print(f"✅ Synced {len(synced)} global slash command(s)")
        except Exception as e:
            print(f"❌ Failed to sync slash commands: {e}")

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
        
        is_mentioned = False
        if bot.user:
            is_mentioned = any(u.id == bot.user.id for u in message.mentions)
        
        # CHỈ tự động nạp kiến thức nếu đây KHÔNG PHẢI là câu hỏi (không tag Bot)
        if is_knowledge_channel and not is_mentioned:
            # 1. Check if user has sufficient permissions (Manage Channels or Administrator)
            is_authorized = False
            if hasattr(message.author, 'guild_permissions'):
                perms = message.author.guild_permissions
                is_authorized = getattr(perms, 'administrator', False) or getattr(perms, 'manage_channels', False)
            
            if not is_authorized:
                logger.debug(f"Ignored ingestion: Message from {message.author} in #{channel_name} (Insufficient permissions)")
            else:
                try:
                    chunk_ids, chunks_text, metadatas = await prepare_discord_message(
                        message_id=str(message.id),
                        content=message.content,
                        attachments=message.attachments,
                        channel_name=getattr(message.channel, 'name', 'unknown'),
                        author=str(message.author.display_name or message.author.name),
                        created_at=message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        jump_url=message.jump_url
                    )

                    if chunk_ids:
                        upsert_documents(chunk_ids, chunks_text, metadatas)
                        logger.info(f"Successfully auto-ingested message ID {message.id} from #{channel_name} (Author: {message.author})")
                except Exception as e:
                    logger.error(f"Error during auto-ingestion for message {message.id}: {e}", exc_info=True)

        # Logic 2: QA RAG Response ONLY when @Mentioned
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
                        if answer == DEFAULT_FALLBACK:
                            expert_tag = route_to_expert(user_query)
                            if expert_tag:
                                experts = experts_db.get_experts_by_tag(expert_tag)
                                if experts:
                                    mentions = " ".join([f"<@{u}>" for u in experts])
                                    reply_text = f"Em chưa tìm thấy thông tin này trong tài liệu. Tuy nhiên, em nhận thấy câu hỏi liên quan đến **{expert_tag}**. Nhờ chuyên gia {mentions} vào hỗ trợ bạn nhé!"
                        elif sources:
                            reply_text += "\n\n📌 **Nguồn tham khảo:**\n" + "\n".join([f"• {src}" for src in sources])

                        if len(reply_text) <= 2000:
                            await message.reply(reply_text, mention_author=True)
                        else:
                            # Cắt nhỏ tin nhắn nếu dài hơn 2000 ký tự (Giới hạn của Discord)
                            chunks = [reply_text[i:i+1900] for i in range(0, len(reply_text), 1900)]
                            await message.reply(chunks[0], mention_author=True)
                            for chunk in chunks[1:]:
                                await message.channel.send(chunk)
            except Exception as e:
                logger.error(f"Error processing QA message {message.id}: {e}", exc_info=True)
                await message.reply("⚠️ Có lỗi xảy ra khi xử lý câu hỏi của bạn. Vui lòng thử lại sau!", mention_author=True)

        # Process any command decorators registered on the bot
        await bot.process_commands(message)

    @bot.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        # Ignore bot's own reactions
        if payload.member and payload.member.bot:
            return

        # Check if emoji is the designated curation emoji
        if payload.emoji.name != settings.CURATION_EMOJI:
            return

        # Check for Administrator or Manage Channels permissions
        if not payload.member:
            return
            
        perms = payload.member.guild_permissions
        is_authorized = getattr(perms, 'administrator', False) or getattr(perms, 'manage_channels', False)
        
        if not is_authorized:
            return

        try:
            channel = bot.get_channel(payload.channel_id)
            if not channel:
                channel = await bot.fetch_channel(payload.channel_id)

            # Prevent duplicate ingestion: Ignore reactions in auto-ingest Knowledge channels
            channel_topic = getattr(channel, 'topic', '') or ''
            if hasattr(channel, 'parent') and channel.parent:
                parent_topic = getattr(channel.parent, 'topic', '') or ''
                channel_topic = f"{channel_topic} {parent_topic}"
            
            if settings.KNOWLEDGE_TOPIC_TAG in channel_topic.upper():
                return
                
            message = await channel.fetch_message(payload.message_id)

            # Determine context based on whether it is a reply
            final_content = message.content
            if message.reference and message.reference.message_id:
                try:
                    original_msg = await channel.fetch_message(message.reference.message_id)
                    final_content = f"Câu hỏi: {original_msg.content}\nTrả lời: {message.content}"
                except Exception as e:
                    logger.warning(f"Could not fetch original message for reply {message.id}: {e}")

            # Ingest to Vector DB
            chunk_ids, chunks_text, metadatas = await prepare_discord_message(
                message_id=f"curated_{message.id}",
                content=final_content,
                attachments=message.attachments,
                channel_name=getattr(channel, 'name', 'unknown'),
                author=str(message.author.display_name or message.author.name),
                created_at=message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                jump_url=message.jump_url
            )

            if chunk_ids:
                upsert_documents(chunk_ids, chunks_text, metadatas)
                logger.info(f"Curated message ID {message.id} via reaction by {payload.member.display_name}")
                await message.reply(f"✅ Đã ghi nhận kiến thức này vào RAG! (Được duyệt bởi <@{payload.member.id}>)", mention_author=False)

        except Exception as e:
            logger.error(f"Error during reaction curation: {e}", exc_info=True)

    @bot.event
    async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
        if payload.emoji.name != settings.CURATION_EMOJI:
            return

        try:
            guild = bot.get_guild(payload.guild_id)
            if not guild:
                return
                
            member = guild.get_member(payload.user_id)
            if not member:
                member = await guild.fetch_member(payload.user_id)
                
            if member.bot:
                return

            perms = member.guild_permissions
            is_authorized = getattr(perms, 'administrator', False) or getattr(perms, 'manage_channels', False)
            
            if not is_authorized:
                return

            channel = bot.get_channel(payload.channel_id)
            if not channel:
                channel = await bot.fetch_channel(payload.channel_id)

            channel_topic = getattr(channel, 'topic', '') or ''
            if hasattr(channel, 'parent') and channel.parent:
                parent_topic = getattr(channel.parent, 'topic', '') or ''
                channel_topic = f"{channel_topic} {parent_topic}"
            
            if settings.KNOWLEDGE_TOPIC_TAG in channel_topic.upper():
                return
                
            delete_document(f"curated_{payload.message_id}")
            logger.info(f"Curated message ID {payload.message_id} removed via un-reaction by {member.display_name}")
            
            message = await channel.fetch_message(payload.message_id)
            await channel.send(f"🗑️ Đã thu hồi kiến thức (Do <@{member.id}> bỏ duyệt).", reference=message, mention_author=False)
            
        except Exception as e:
            logger.error(f"Error during reaction removal curation: {e}", exc_info=True)

    @bot.event
    async def on_message_edit(before: discord.Message, after: discord.Message):
        if after.author.bot:
            return

        channel_topic = getattr(after.channel, 'topic', '') or ''
        if hasattr(after.channel, 'parent') and after.channel.parent:
            parent_topic = getattr(after.channel.parent, 'topic', '') or ''
            channel_topic = f"{channel_topic} {parent_topic}"
        
        if settings.KNOWLEDGE_TOPIC_TAG in channel_topic.upper():
            is_mentioned = False
            if bot.user:
                is_mentioned = any(u.id == bot.user.id for u in after.mentions)
                
            if is_mentioned:
                return

            is_authorized = False
            if hasattr(after.author, 'guild_permissions'):
                perms = after.author.guild_permissions
                is_authorized = getattr(perms, 'administrator', False) or getattr(perms, 'manage_channels', False)
            
            if is_authorized:
                chunk_ids, chunks_text, metadatas = await prepare_discord_message(
                    message_id=str(after.id),
                    content=after.content,
                    attachments=after.attachments,
                    channel_name=getattr(after.channel, 'name', 'unknown'),
                    author=str(after.author.display_name or after.author.name),
                    created_at=after.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    jump_url=after.jump_url
                )
                if chunk_ids:
                    upsert_documents(chunk_ids, chunks_text, metadatas)
                    logger.info(f"Updated message ID {after.id} in ChromaDB")

    @bot.event
    async def on_message_delete(message: discord.Message):
        if message.author.bot:
            return

        channel_topic = getattr(message.channel, 'topic', '') or ''
        if hasattr(message.channel, 'parent') and message.channel.parent:
            parent_topic = getattr(message.channel.parent, 'topic', '') or ''
            channel_topic = f"{channel_topic} {parent_topic}"
        
        if settings.KNOWLEDGE_TOPIC_TAG in channel_topic.upper():
            delete_document(str(message.id))
            logger.info(f"Deleted message ID {message.id} from ChromaDB due to Discord deletion")

    @bot.command(name='sync_history')
    @commands.has_permissions(administrator=True)
    async def sync_history(ctx, limit: int = 100):
        channel_topic = getattr(ctx.channel, 'topic', '') or ''
        if hasattr(ctx.channel, 'parent') and ctx.channel.parent:
            parent_topic = getattr(ctx.channel.parent, 'topic', '') or ''
            channel_topic = f"{channel_topic} {parent_topic}"
            
        if settings.KNOWLEDGE_TOPIC_TAG not in channel_topic.upper():
            await ctx.reply("⚠️ Lệnh này chỉ dùng được trong kênh KNOWLEDGE!")
            return
            
        await ctx.reply(f"🔄 Đang lội ngược dòng để cào tối đa {limit} tin nhắn cũ... Quá trình này có thể mất vài phút.")
        count = 0
        async for msg in ctx.channel.history(limit=limit):
            if msg.author.bot or not msg.content.strip():
                continue
                
            is_mentioned = False
            if bot.user:
                is_mentioned = any(u.id == bot.user.id for u in msg.mentions)
                
            if is_mentioned:
                continue

            is_authorized = False
            if hasattr(msg.author, 'guild_permissions'):
                perms = msg.author.guild_permissions
                is_authorized = getattr(perms, 'administrator', False) or getattr(perms, 'manage_channels', False)
                
            if is_authorized:
                chunk_ids, chunks_text, metadatas = await prepare_discord_message(
                    message_id=str(msg.id),
                    content=msg.content,
                    attachments=msg.attachments,
                    channel_name=getattr(ctx.channel, 'name', 'unknown'),
                    author=str(msg.author.display_name or msg.author.name),
                    created_at=msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    jump_url=msg.jump_url
                )
                if chunk_ids:
                    upsert_documents(chunk_ids, chunks_text, metadatas)
                    count += 1
                    
        await ctx.reply(f"✅ Đã quét xong. Nạp thành công {count} tin nhắn vào Não bộ RAG.")

    @bot.tree.command(name="ask", description="Hỏi Kudo Bot (Câu trả lời sẽ được ẩn, chỉ mình bạn thấy)")
    @app_commands.describe(question="Nhập câu hỏi của bạn vào đây")
    async def ask_command(interaction: discord.Interaction, question: str):
        # Trả lời tức thì để tránh Discord báo lỗi "This interaction failed" (vì RAG xử lý lâu)
        await interaction.response.defer(ephemeral=True)
        
        try:
            answer, sources = generate_rag_answer(question)
            
            reply_text = answer
            if answer == DEFAULT_FALLBACK:
                expert_tag = route_to_expert(question)
                if expert_tag:
                    experts = experts_db.get_experts_by_tag(expert_tag)
                    if experts:
                        mentions = " ".join([f"<@{u}>" for u in experts])
                        reply_text = f"Em chưa tìm thấy thông tin này trong tài liệu. Tuy nhiên, em nhận thấy câu hỏi liên quan đến **{expert_tag}**. Nhờ chuyên gia {mentions} vào hỗ trợ bạn nhé!"
            elif sources:
                reply_text += "\n\n📌 **Nguồn tham khảo:**\n" + "\n".join([f"• {src}" for src in sources])
            
            # Cắt nhỏ tin nhắn nếu dài hơn 2000 ký tự
            if len(reply_text) <= 2000:
                await interaction.followup.send(reply_text, ephemeral=True)
            else:
                chunks = [reply_text[i:i+1900] for i in range(0, len(reply_text), 1900)]
                for chunk in chunks:
                    await interaction.followup.send(chunk, ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Error in /ask command: {e}", exc_info=True)
            await interaction.followup.send("⚠️ Có lỗi xảy ra khi xử lý câu hỏi của bạn. Vui lòng thử lại sau!", ephemeral=True)

    @bot.tree.command(name="tong_hop", description="Tổng hợp nhanh các thông báo trong kênh")
    @app_commands.describe(days="Số ngày muốn tổng hợp (mặc định 1 ngày, tối đa 30 ngày)")
    async def tong_hop_command(interaction: discord.Interaction, days: int = 1):
        if days < 1 or days > 30:
            await interaction.response.send_message("⚠️ Số ngày tổng hợp phải từ 1 đến 30 ngày.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=False) # Để mọi người cùng đọc
        
        try:
            from datetime import datetime, timedelta, timezone
            after_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Thu thập tin nhắn (limit=200 để lấy đủ số lượng tin nhắn trong nhiều ngày)
            messages = []
            async for msg in interaction.channel.history(limit=200, after=after_date):
                if not msg.author.bot and msg.content.strip():
                    # Thêm ngày tháng để AI dễ tóm tắt
                    date_str = msg.created_at.strftime("%d/%m")
                    messages.append(f"[{date_str}] [{msg.author.display_name}]: {msg.content}")
            
            if not messages:
                await interaction.followup.send(f"Không có thông báo nào trong {days} ngày qua.")
                return
                
            full_text = "\n".join(messages)
            
            # Gửi cho Gemini tóm tắt
            summary = summarize_text(f"Hãy tóm tắt các sự kiện trong {days} ngày qua:\n{full_text}")
            
            reply_text = f"📢 **TỔNG HỢP THÔNG BÁO #{interaction.channel.name} ({days} NGÀY QUA)**\n\n{summary}"
            
            if len(reply_text) <= 2000:
                await interaction.followup.send(reply_text)
            else:
                chunks = [reply_text[i:i+1900] for i in range(0, len(reply_text), 1900)]
                for chunk in chunks:
                    await interaction.followup.send(chunk)
                    
        except Exception as e:
            logger.error(f"Error in /tong_hop command: {e}", exc_info=True)
            await interaction.followup.send("⚠️ Có lỗi xảy ra khi tổng hợp thông tin.", ephemeral=True)

    async def tag_autocomplete(
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        tags = experts_db.get_all_tags()
        # Filter based on user's current input and limit to 25 choices (Discord API limit)
        choices = [
            app_commands.Choice(name=tag, value=tag)
            for tag in tags if current.lower() in tag.lower()
        ][:25]
        return choices

    @bot.tree.command(name="add_expert", description="[Admin] Gắn lĩnh vực chuyên môn cho một thành viên BTC")
    @app_commands.describe(user="Thành viên BTC", tag="Lĩnh vực (vd: kỹ_thuật, hậu_cần, hành_chính)")
    @app_commands.autocomplete(tag=tag_autocomplete)
    @app_commands.default_permissions(administrator=True)
    async def add_expert_command(interaction: discord.Interaction, user: discord.Member, tag: str):
        experts_db.add_expert(tag, str(user.id))
        await interaction.response.send_message(f"✅ Đã gán lĩnh vực `{tag}` cho {user.mention}.", ephemeral=True)

    @bot.tree.command(name="remove_expert", description="[Admin] Gỡ lĩnh vực chuyên môn của một thành viên")
    @app_commands.describe(user="Thành viên BTC", tag="Lĩnh vực cần gỡ")
    @app_commands.autocomplete(tag=tag_autocomplete)
    @app_commands.default_permissions(administrator=True)
    async def remove_expert_command(interaction: discord.Interaction, user: discord.Member, tag: str):
        success = experts_db.remove_expert(tag, str(user.id))
        if success:
            await interaction.response.send_message(f"✅ Đã gỡ lĩnh vực `{tag}` khỏi {user.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ Không tìm thấy lĩnh vực `{tag}` cho {user.mention}.", ephemeral=True)

    @bot.tree.command(name="list_experts", description="Xem danh sách Danh bạ Chuyên gia hiện tại")
    async def list_experts_command(interaction: discord.Interaction):
        db = experts_db.get_full_db()
        if not db:
            await interaction.response.send_message("Danh bạ chuyên gia hiện đang trống.", ephemeral=True)
            return
            
        lines = ["📋 **DANH BẠ CHUYÊN GIA (EXPERT DIRECTORY)**"]
        for tag, users in db.items():
            mentions = ", ".join([f"<@{u}>" for u in users])
            lines.append(f"• **{tag}**: {mentions}")
            
        await interaction.response.send_message("\n".join(lines), ephemeral=True)
