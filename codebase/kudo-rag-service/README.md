# 🤖 Kudo RAG Service (Discord Bot Assistant)

**Kudo RAG Service** là một trợ lý ảo tự động trên Discord dành cho cộng đồng học tập AI (AI20K), được xây dựng dựa trên công nghệ **RAG** (Retrieval-Augmented Generation) kết hợp với **Google Gemini (gemini-2.5-flash)** và cơ sở dữ liệu vector **ChromaDB**.

---

## 🎯 1. Bot này để làm gì? (Mục đích)
Bot được sinh ra để đóng vai trò như một "Thư viện viên" và "Trợ giảng" mẫn cán trong server Discord của cộng đồng AI20K. 
Thay vì học viên phải lướt lại hàng trăm tin nhắn cũ để tìm tài liệu hoặc hỏi đi hỏi lại những vấn đề đã được giải đáp, Bot sẽ **tự động học (đọc)** các kiến thức từ các kênh quan trọng và **trả lời ngay lập tức** khi có người hỏi.

## 💡 2. Giải quyết vấn đề gì?
Trong các cộng đồng học tập đông thành viên trên Discord (như AI20K), các vấn đề thường gặp bao gồm:
- **Trôi tin nhắn:** Tài liệu, bài giảng hay, thông báo quan trọng thường bị trôi mất do lượng tin nhắn chat quá nhiều.
- **Hỏi lại câu hỏi cũ:** Người mới tham gia hoặc học viên hay hỏi lại những câu hỏi đã được giải đáp trước đó, làm tốn thời gian của mentor/admin.
- **Khó tìm kiếm:** Tính năng search của Discord chưa đủ thông minh để hiểu ngữ nghĩa (semantic search) câu hỏi của người dùng.

👉 **Giải pháp của Kudo RAG:** Bot tự động lưu trữ kiến thức và trả lời câu hỏi của người dùng ngay lập tức, chính xác, có kèm theo **đường link trích dẫn (jump url)** về bài viết gốc để người dùng có thể đọc thêm chi tiết. Điều này giúp tiết kiệm thời gian cho Mentor và hỗ trợ học viên 24/7.

## ✨ 3. Các chức năng chính
- **🧠 Tự động thu thập kiến thức (Knowledge Ingestion):** Lắng nghe và tự động "đọc" các tin nhắn từ các kênh kiến thức (VD: `#thông-báo`, `#tài-nguyên`, `#bài-học`, `#lý-thuyết`). Các nội dung này được chuyển hóa thành Vector (Embeddings) và lưu vào cơ sở dữ liệu ChromaDB, kèm theo siêu dữ liệu (metadata như tác giả, thời gian, link tin nhắn).
- **💬 Trả lời câu hỏi thông minh (RAG QA Assistance):** Khi người dùng đặt câu hỏi trong các kênh `#hỏi-đáp`, `#gõ-command`, `#chung` hoặc trực tiếp `@tag` bot, bot sẽ:
  1. Tìm kiếm các tài liệu liên quan nhất trong ChromaDB.
  2. Tổng hợp câu trả lời thông minh dựa trên kiến thức tìm được (bằng Google Gemini).
  3. Phản hồi kèm theo trích dẫn nguồn (link bài viết gốc).
- **🛡️ Tránh ảo giác (Anti-Hallucination):** Bot được thiết lập với bộ prompt nghiêm ngặt để chỉ trả lời dựa trên ngữ cảnh đã tìm thấy trong Server, giảm thiểu tối đa việc AI bịa ra câu trả lời sai.

---

## 🚀 4. Làm thế nào để Test / Chạy thử bot?

### 🛠️ Yêu cầu hệ thống
- Python 3.10+
- Token Discord Bot & API Key Google Gemini.

### ⚙️ Bước 1: Cài đặt môi trường
Mở terminal và chạy các lệnh sau:
```bash
# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường (Windows PowerShell)
.venv\Scripts\Activate.ps1
# Nếu dùng Linux/macOS: source .venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### 🔑 Bước 2: Thiết lập biến môi trường
Copy file `.env.example` thành `.env` và điền các thông tin bí mật của bạn:
```bash
cp .env.example .env
```
Nội dung file `.env` cần có:
- `DISCORD_TOKEN`: Lấy từ Discord Developer Portal.
- `GEMINI_API_KEY`: Lấy từ Google AI Studio.
- `SANDBOX_GUILD_ID`: ID của Server Discord dùng để test.
- `CHROMA_HOST` & `CHROMA_PORT`: Cấu hình cho ChromaDB.

### 🏃 Bước 3: Chạy Bot (Dành cho Development & Test)
Vì dự án dùng kiến trúc Client-Server cho cơ sở dữ liệu Vector, bạn cần mở **2 Terminal** để chạy song song:

**Terminal 1: Khởi động ChromaDB Server**
```bash
# Chạy DB ở port 8000
chroma run --path ./chroma_db
```

**Terminal 2: Khởi động Bot Discord**
```bash
# Đảm bảo đã activate môi trường ảo
python main.py
```

### 🧪 Bước 4: Hướng dẫn Test thực tế trên Discord
1. **Test tính năng Ingestion (Học kiến thức):** 
   - Vào kênh `#thông-báo` hoặc `#tài-nguyên` trong server Sandbox của bạn.
   - Nhắn một tin nhắn chứa kiến thức (Ví dụ: *"Lịch học tuần này là thứ 3 và thứ 5 lúc 20h. Các bạn chú ý tham gia đầy đủ"*). Bot sẽ ngầm đọc và lưu vào Database.
2. **Test tính năng QA (Hỏi đáp):**
   - Vào kênh `#hỏi-đáp` hoặc `@tag` bot.
   - Hỏi bot: *"Lịch học tuần này là vào thứ mấy?"*
   - Bot sẽ trả lời: *"Lịch học tuần này là thứ 3 và thứ 5 lúc 20h"* kèm theo **link dẫn đến tin nhắn gốc** mà bạn vừa tạo ở trên.

---

## 📦 5. Triển khai lên Production (Docker)
Để hệ thống chạy ổn định 24/7 trên Server/VPS, bạn nên sử dụng Docker Compose.
```bash
# Khởi chạy toàn bộ hệ thống ngầm
docker-compose up -d

# Xem log hoạt động của bot
docker-compose logs -f kudo_bot
```
