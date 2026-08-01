import logging
import discord
from discord import app_commands
from discord.ext import commands
from config import settings
from core.ingestion import prepare_discord_message, is_quality_knowledge_content
from core.extractors import process_attachments
from core.vector_store import (
    upsert_documents, delete_document, get_documents_by_message_id, delete_documents_by_message_id,
    async_upsert_documents, async_delete_document, async_get_documents_by_message_id, async_delete_documents_by_message_id
)
from core.rag_chain import (
    generate_rag_answer, summarize_text, route_to_expert, DEFAULT_FALLBACK, synthesize_thread_answers,
    async_generate_rag_answer, async_summarize_text, async_route_to_expert, async_synthesize_thread_answers, async_generate_rag_answer_with_trace
)
from core import experts_db
from core import nosql_db
from core.guardrails import check_user_cooldown

logger = logging.getLogger(__name__)

# --- THEME & UI CONSTANTS ---
class UI_COLORS:
    SUCCESS = 0x2ECC71     # Xanh lá (Trả lời RAG thành công)
    WARNING = 0xF1C40F     # Vàng (Không tìm thấy, gọi chuyên gia)
    INFO = 0x3498DB        # Xanh dương (Dashboard, Stats)
    DIAGNOSTIC = 0x9B59B6  # Tím (Profiler, Trace)

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
                    # 1. Thả reaction ⏳ báo hiệu Bot đang bắt đầu xử lý bất đồng bộ
                    try:
                        await message.add_reaction("⏳")
                    except Exception:
                        pass

                    chunk_ids, chunks_text, metadatas = await prepare_discord_message(
                        message_id=str(message.id),
                        content=message.content,
                        attachments=message.attachments,
                        channel_name=getattr(message.channel, 'name', 'unknown'),
                        author=str(message.author.display_name or message.author.name),
                        created_at=settings.format_datetime_gmt7(message.created_at),
                        jump_url=message.jump_url
                    )

                    if chunk_ids:
                        await async_upsert_documents(chunk_ids, chunks_text, metadatas)
                        logger.info(f"Successfully auto-ingested message ID {message.id} from #{channel_name} (Author: {message.author})")
                        
                        # Xử lý xong: Đổi reaction ⏳ sang ✅
                        try:
                            if bot.user:
                                await message.remove_reaction("⏳", bot.user)
                            await message.add_reaction("✅")
                        except Exception:
                            pass
                    else:
                        # Không có nội dung chất lượng để nạp (Noise filter / rác) -> Gỡ ⏳
                        try:
                            if bot.user:
                                await message.remove_reaction("⏳", bot.user)
                        except Exception:
                            pass
                except Exception as e:
                    logger.error(f"Error during auto-ingestion for message {message.id}: {e}", exc_info=True)
                    try:
                        if bot.user:
                            await message.remove_reaction("⏳", bot.user)
                    except Exception:
                        pass

        # Logic 2: QA RAG Response ONLY when @Mentioned
        if is_mentioned:
            # Per-User Cooldown Rate Limiter Check
            is_allowed, remaining = check_user_cooldown(str(message.author.id))
            if not is_allowed:
                await message.reply(f"⏳ Bạn thao tác quá nhanh! Vui lòng chờ {remaining}s nữa trước khi hỏi tiếp nhé.", mention_author=True)
                return

            try:
                async with message.channel.typing():
                    # Clean bot mention from content string
                    user_query = message.content
                    if bot.user:
                        user_query = user_query.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "")
                    user_query = user_query.strip()

                    if not user_query:
                        await message.reply("Vui lòng nhập câu hỏi sau khi tag mình nhé! (VD: `@Kudo Bot Kafka là gì?`)", mention_author=True)
                        return
                    
                    if user_query:
                        answer, sources = await async_generate_rag_answer(user_query)

                        if answer == DEFAULT_FALLBACK:
                            expert_tag = await async_route_to_expert(user_query)
                            mentions = ""
                            if expert_tag:
                                experts = experts_db.get_experts_by_tag(expert_tag)
                                if experts:
                                    mentions = " ".join([f"<@{u}>" for u in experts])
                            
                            embed = discord.Embed(
                                title="🔍 Chưa tìm thấy thông tin trực tiếp",
                                description=f"Em chưa tìm thấy thông tin này trong tài liệu." + (f"\n\n👉 Nhờ chuyên gia **{expert_tag}** hỗ trợ: {mentions}" if mentions else ""),
                                color=UI_COLORS.WARNING
                            )
                            embed.set_footer(text="HAX Rule G10 & G2 • Chuyển giao Chuyên gia")
                            await message.reply(embed=embed, mention_author=True)
                        else:
                            main_desc = answer[:3900] + ("\n\n*(Xem tiếp nội dung phía dưới...)*" if len(answer) > 3900 else "")
                            embed = discord.Embed(
                                title="🤖 Kudo Assistant - Phản hồi Tri thức",
                                description=main_desc,
                                color=UI_COLORS.SUCCESS
                            )
                            if sources:
                                formatted_src = "\n".join([f"• {src}" for src in sources])
                                embed.add_field(name="📌 Nguồn tham khảo", value=formatted_src[:1024], inline=False)
                            embed.set_footer(text="Powered by Gemini 2.5 Flash & ChromaDB • Kudo RAG Service")
                            await message.reply(embed=embed, mention_author=True)

                            if len(answer) > 3900:
                                remaining = answer[3900:]
                                chunks = [remaining[i:i+4000] for i in range(0, len(remaining), 4000)]
                                for i, chunk in enumerate(chunks):
                                    follow_embed = discord.Embed(description=chunk, color=UI_COLORS.SUCCESS)
                                    await message.channel.send(embed=follow_embed)


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

            # 1. Xác định Parent_ID và lưu vào NoSQL
            parent_id = str(message.id)
            original_content = ""
            channel_name = getattr(channel, 'name', 'unknown')
            all_attachments = list(message.attachments)
            
            if isinstance(channel, discord.Thread):
                parent_id = f"thread_{channel.id}"
                try:
                    original_msg = await channel.fetch_message(channel.id)
                    original_content = f"Chủ đề [{channel.name}]: {original_msg.content}"
                    if original_msg.attachments:
                        all_attachments.extend(original_msg.attachments)
                except Exception:
                    original_content = f"Chủ đề [{channel.name}]"
            elif message.reference and message.reference.message_id:
                parent_id = f"reply_{message.reference.message_id}"
                try:
                    original_msg = await channel.fetch_message(message.reference.message_id)
                    original_content = f"Câu hỏi gốc: {original_msg.content}"
                    if original_msg.attachments:
                        all_attachments.extend(original_msg.attachments)
                except Exception as e:
                    logger.warning(f"Could not fetch original message {message.reference.message_id}")
            
            # Ghi vào DB
            nosql_db.upsert_message(
                parent_id=parent_id, 
                message_id=str(message.id), 
                content=message.content, 
                author=str(message.author.display_name or message.author.name)
            )
            
            # 2. Lấy toàn bộ anh em và tổng hợp
            active_messages = nosql_db.get_active_messages(parent_id)
            
            if not active_messages:
                return # Mặc dù vừa add nhưng ko hiểu sao rỗng
                
            if len(active_messages) > 1:
                logger.info(f"Synthesizing {len(active_messages)} active chunks for {parent_id}.")
                synthesized = await async_synthesize_thread_answers(active_messages[:-1], active_messages[-1])
            else:
                synthesized = active_messages[0]
                
            final_content = f"{original_content}\n\nGiải pháp/Trả lời (Đã tổng hợp):\n{synthesized}" if original_content else f"Nội dung được lưu: {synthesized}"
            
            target_message_id = f"synthesized_{parent_id}"
            
            # Xóa các chunk cũ của parent_id này trước khi lưu đè
            await async_delete_documents_by_message_id(target_message_id)

            # Ingest to Vector DB
            chunk_ids, chunks_text, metadatas = await prepare_discord_message(
                message_id=target_message_id,
                content=final_content,
                attachments=all_attachments,
                channel_name=channel_name,
                author="System Synthesizer",
                created_at=settings.format_datetime_gmt7(message.created_at),
                jump_url=message.jump_url
            )

            if chunk_ids:
                await async_upsert_documents(chunk_ids, chunks_text, metadatas)
                logger.info(f"Upserted unified chunk {target_message_id} via reaction by {payload.member.display_name}")
                try:
                    confirm_msg = await message.reply(
                        f"✅ Đã ghi nhận và tổng hợp kiến thức vào RAG! (Được duyệt bởi <@{payload.member.id}>)",
                        mention_author=False
                    )
                    await confirm_msg.delete(delay=7)
                except Exception as err:
                    logger.debug(f"Could not send/delete reaction curation notification: {err}")

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
            message = await channel.fetch_message(payload.message_id)
            
            # 1. Xác định Parent_ID và lưu vào NoSQL
            parent_id = str(message.id)
            original_content = ""
            channel_name = getattr(channel, 'name', 'unknown')
            all_attachments = list(message.attachments)
            
            if isinstance(channel, discord.Thread):
                parent_id = f"thread_{channel.id}"
                try:
                    original_msg = await channel.fetch_message(channel.id)
                    original_content = f"Chủ đề [{channel.name}]: {original_msg.content}"
                    if original_msg.attachments:
                        all_attachments.extend(original_msg.attachments)
                except Exception:
                    original_content = f"Chủ đề [{channel.name}]"
            elif message.reference and message.reference.message_id:
                parent_id = f"reply_{message.reference.message_id}"
                try:
                    original_msg = await channel.fetch_message(message.reference.message_id)
                    original_content = f"Câu hỏi gốc: {original_msg.content}"
                    if original_msg.attachments:
                        all_attachments.extend(original_msg.attachments)
                except Exception as e:
                    pass
            
            # 2. Xóa mềm trong DB
            nosql_db.soft_delete_message(parent_id, str(message.id))
            
            # 3. Quét lại tình hình anh em
            active_messages = nosql_db.get_active_messages(parent_id)
            target_message_id = f"synthesized_{parent_id}"
            
            await async_delete_documents_by_message_id(target_message_id)
            
            if active_messages:
                # Vẫn còn bình luận đúng -> Tổng hợp lại các bình luận còn lại
                if len(active_messages) > 1:
                    synthesized = await async_synthesize_thread_answers(active_messages[:-1], active_messages[-1])
                else:
                    synthesized = active_messages[0]
                    
                final_content = f"{original_content}\n\nGiải pháp/Trả lời (Đã tổng hợp):\n{synthesized}" if original_content else f"Nội dung được lưu: {synthesized}"
                
                chunk_ids, chunks_text, metadatas = await prepare_discord_message(
                    message_id=target_message_id,
                    content=final_content,
                    attachments=all_attachments,
                    channel_name=channel_name,
                    author="System Synthesizer",
                    created_at=settings.format_datetime_gmt7(message.created_at),
                    jump_url=message.jump_url
                )
                if chunk_ids:
                    await async_upsert_documents(chunk_ids, chunks_text, metadatas)
                logger.info(f"Re-synthesized chunk {target_message_id} after removing message {payload.message_id}")
            else:
                logger.info(f"Deleted chunk {target_message_id} because all curations were removed.")
                
            logger.info(f"Curated message ID {payload.message_id} removed via un-reaction by {member.display_name}")
            message = await channel.fetch_message(payload.message_id)
            try:
                confirm_msg = await channel.send(
                    f"🗑️ Đã thu hồi kiến thức (Do <@{member.id}> bỏ duyệt).",
                    reference=message,
                    mention_author=False
                )
                await confirm_msg.delete(delay=7)
            except Exception as err:
                logger.debug(f"Could not send/delete reaction removal notification: {err}")
            
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
                    created_at=settings.format_datetime_gmt7(after.created_at),
                    jump_url=after.jump_url
                )
                if chunk_ids:
                    await async_upsert_documents(chunk_ids, chunks_text, metadatas)
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
            await async_delete_document(str(message.id))
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
            # Ignored bot messages or messages with neither content nor attachments
            if msg.author.bot or (not msg.content.strip() and not msg.attachments):
                continue
                
            is_mentioned = False
            if bot.user:
                is_mentioned = any(u.id == bot.user.id for u in msg.mentions)
                
            if is_mentioned:
                continue

            chunk_ids, chunks_text, metadatas = await prepare_discord_message(
                message_id=str(msg.id),
                content=msg.content,
                attachments=msg.attachments,
                channel_name=getattr(ctx.channel, 'name', 'unknown'),
                author=str(msg.author.display_name or msg.author.name),
                created_at=settings.format_datetime_gmt7(msg.created_at),
                jump_url=msg.jump_url
            )
            if chunk_ids:
                await async_upsert_documents(chunk_ids, chunks_text, metadatas)
                count += 1

                    
        await ctx.reply(f"✅ Đã quét xong. Nạp thành công {count} tin nhắn vào Não bộ RAG.")

    @bot.tree.command(name="ask", description="Hỏi Kudo Bot (Câu trả lời sẽ được ẩn, chỉ mình bạn thấy)")
    @app_commands.describe(question="Nhập câu hỏi của bạn vào đây")
    async def ask_command(interaction: discord.Interaction, question: str):
        # Per-User Cooldown Rate Limiter Check
        is_allowed, remaining = check_user_cooldown(str(interaction.user.id))
        if not is_allowed:
            await interaction.response.send_message(f"⏳ Bạn thao tác quá nhanh! Vui lòng chờ {remaining}s nữa trước khi hỏi câu tiếp theo nhé.", ephemeral=True)
            return

        # Trả lời tức thì để tránh Discord báo lỗi "This interaction failed" (vì RAG xử lý lâu)
        await interaction.response.defer(ephemeral=True)
        
        try:
            answer, sources = await async_generate_rag_answer(question)
            
            reply_text = answer
            if answer == DEFAULT_FALLBACK:
                expert_tag = await async_route_to_expert(question)
                if expert_tag:
                    experts = experts_db.get_experts_by_tag(expert_tag)
                    if experts:
                        mentions = " ".join([f"<@{u}>" for u in experts])
                        reply_text = f"Em chưa tìm thấy thông tin này trong tài liệu. Tuy nhiên, em nhận thấy câu hỏi liên quan đến **{expert_tag}**. Nhờ chuyên gia {mentions} vào hỗ trợ bạn nhé!"
            elif sources:
                reply_text += "\n\n📌 **Nguồn tham khảo:**\n" + "\n".join([f"• {src}" for src in sources])
            
            # Cắt nhỏ tin nhắn bằng Embed nếu dài
            if len(reply_text) <= 3900:
                embed = discord.Embed(description=reply_text, color=UI_COLORS.SUCCESS)
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                chunks = [reply_text[i:i+4000] for i in range(0, len(reply_text), 4000)]
                for chunk in chunks:
                    embed = discord.Embed(description=chunk, color=UI_COLORS.SUCCESS)
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Error in /ask command: {e}", exc_info=True)
            await interaction.followup.send("⚠️ Có lỗi xảy ra khi xử lý câu hỏi của bạn. Vui lòng thử lại sau!", ephemeral=True)

    @bot.tree.command(name="tong_hop", description="Tổng hợp nhanh các thông báo & tin tức hot trong kênh (Có lọc rác & bóc file/ảnh)")
    @app_commands.describe(days="Số ngày muốn tổng hợp (mặc định 1 ngày, tối đa 30 ngày)")
    async def tong_hop_command(interaction: discord.Interaction, days: int = 1):
        if days < 1 or days > 30:
            await interaction.response.send_message("⚠️ Số ngày tổng hợp phải từ 1 đến 30 ngày.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=False) # Để mọi người cùng đọc
        
        try:
            from datetime import datetime, timedelta, timezone
            after_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            messages = []
            total_chars = 0
            
            # Quét tất cả tin nhắn trong N ngày qua (Dynamic Window)
            async for msg in interaction.channel.history(limit=500, after=after_date):
                # 1. Bỏ qua tin nhắn của Bot & lọc rác dữ liệu (Noise filter)
                if msg.author.bot:
                    continue
                    
                if not is_quality_knowledge_content(msg.content, msg.attachments):
                    continue

                date_str = settings.format_datetime_gmt7(msg.created_at)
                msg_text = msg.content.strip()
                
                # 2. Bóc tách nội dung File đính kèm / Ảnh Poster nếu có
                if msg.attachments:
                    file_text = await process_attachments(msg.attachments)
                    if file_text:
                        msg_text += f"\n[Nội dung File/Ảnh đính kèm]:\n{file_text}"

                formatted_entry = f"[{date_str}] [{msg.author.display_name}]: {msg_text}"
                messages.append(formatted_entry)
                total_chars += len(formatted_entry)
                
                # Giới hạn an toàn 15.000 ký tự để không quá tải Gemini Context
                if total_chars >= 15000:
                    logger.info(f"/tong_hop reached 15,000 character safety cap for channel #{interaction.channel.name}")
                    break
            
            if not messages:
                await interaction.followup.send(f"Không có thông báo hoặc tin tức nổi bật nào trong {days} ngày qua.")
                return
                
            full_text = "\n\n---\n\n".join(messages)
            
            # Gửi cho Gemini tóm tắt chuyên sâu
            summary = await async_summarize_text(f"Hãy tóm tắt và tổng hợp tin tức nổi bật trong {days} ngày qua tại kênh #{interaction.channel.name}:\n\n{full_text}")
            
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

    @bot.tree.command(name="stats", description="Xem chỉ số hoạt động hệ thống Kudo RAG Service")
    async def stats_command(interaction: discord.Interaction):
        try:
            from core.vector_store import collection
            # settings đã được import ở đầu file (from config import settings)
            chunk_count = collection.count()
            tags_count = len(experts_db.get_all_tags())
            ping_ms = round(bot.latency * 1000, 1)
            
            embed = discord.Embed(
                title="📊 TRẠNG THÁI HỆ THỐNG KUDO RAG SERVICE",
                color=UI_COLORS.INFO
            )
            embed.add_field(name="🧠 Vector Store Count", value=f"**{chunk_count}** chunks", inline=True)
            embed.add_field(name="👥 Danh mục Chuyên gia", value=f"**{tags_count}** lĩnh vực", inline=True)
            embed.add_field(name="📶 Discord Gateway Ping", value=f"**{ping_ms}** ms", inline=True)
            embed.add_field(name="⚡ LLM Engine", value=f"`{settings.LLM_MODEL}`", inline=True)
            embed.add_field(name="📌 Embedding Model", value=f"`{settings.EMBEDDING_MODEL}`", inline=True)
            embed.add_field(name="🗄️ ChromaDB Collection", value=f"`{collection.name}`", inline=True)
            embed.set_footer(text="SpaceMarines Team • Live System Telemetry")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in /stats command: {e}")
            await interaction.response.send_message(f"⚠️ Không thể lấy thông số hệ thống: {e}", ephemeral=True)


    @bot.tree.command(name="trace", description="[Profiling] Kiểm tra latency, token usage và luồng logic RAG của một câu hỏi")
    @app_commands.describe(question="Nhập câu hỏi để chạy thử nghiệm profiling")
    async def trace_command(interaction: discord.Interaction, question: str):
        # Per-User Cooldown Rate Limiter Check
        is_allowed, remaining = check_user_cooldown(str(interaction.user.id))
        if not is_allowed:
            await interaction.response.send_message(f"⏳ Bạn thao tác quá nhanh! Vui lòng chờ {remaining}s nữa trước khi thử nghiệm nhé.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            metrics = await async_generate_rag_answer_with_trace(question)
            
            embed = discord.Embed(
                title="🛠️ RAG PIPELINE DIAGNOSTICS & PROFILING",
                color=UI_COLORS.DIAGNOSTIC
            )
            embed.add_field(name="💬 Câu hỏi Test", value=f"*{question[:1024]}*", inline=False)
            
            # Latency field
            latency_text = (
                f"• **Vector DB Search**: `{metrics['retrieval_time_s']}s`\n"
                f"• **Gemini LLM Infer**: `{metrics['llm_time_s']}s`\n"
                f"• **Total Response**: `{metrics['total_time_s']}s` ⚡"
            )
            embed.add_field(name="⏱️ Hiệu năng (Latency)", value=latency_text, inline=False)
            
            # Token usage field
            token_text = (
                f"• **Prompt Tokens**: `{metrics['prompt_tokens']}`\n"
                f"• **Generated Tokens**: `{metrics['candidate_tokens']}`\n"
                f"• **Total Tokens**: `{metrics['total_tokens']}`"
            )
            embed.add_field(name="🧮 Token Usage (`gemini-2.5-flash`)", value=token_text, inline=False)
            
            # Retrieval & Decision
            diag_text = (
                f"• **Chunks Retrieved**: `{metrics['retrieved_chunks_count']}` chunks\n"
                f"• **Decision Route**: `{metrics['decision']}`\n"
                + (f"• **Routed Expert**: `{metrics['expert_tag']}`\n" if metrics['expert_tag'] else "")
            )
            embed.add_field(name="🧠 Diagnostic Route", value=diag_text, inline=False)
            
            # Answer preview inside Embed (max 800 chars for clean UI)
            preview_ans = metrics['answer'][:800] + ("...\n*(Nội dung đầy đủ được gửi nối tiếp ngay bên dưới)*" if len(metrics['answer']) > 800 else "")
            embed.add_field(name="💡 Trích đoạn Phản hồi", value=preview_ans, inline=False)
            
            embed.set_footer(text="Kudo RAG Profiler • Performance & Cost Analytics")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Send full untruncated answer as follow-up Embeds if long
            if len(metrics['answer']) > 800:
                full_text = metrics['answer']
                if metrics['sources']:
                    full_text += "\n\n📌 **Nguồn tham khảo:**\n" + "\n".join([f"• {src}" for src in metrics['sources']])
                
                chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
                for i, chunk in enumerate(chunks):
                    follow_embed = discord.Embed(description=chunk, color=UI_COLORS.DIAGNOSTIC)
                    if i == 0:
                        follow_embed.title = "📄 NỘI DUNG ĐẦY ĐỦ CỦA CÂU TRẢ LỜI"
                    await interaction.followup.send(embed=follow_embed, ephemeral=True)

            
        except Exception as e:
            logger.error(f"Error in /trace command: {e}", exc_info=True)
            await interaction.followup.send(f"⚠️ Lỗi khi chạy profiling: {e}", ephemeral=True)


