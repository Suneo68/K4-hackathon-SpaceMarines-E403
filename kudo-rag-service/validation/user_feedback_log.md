# User Feedback Log - `kudo-rag-service`

This log documents qualitative feedback, empirical scores, and validation interviews from real user interactions in Discord channels.

## 📊 Empirical Feedback Log

| Date (YYYY-MM-DD) | User Handle | Channel | Question Asked | Accuracy Score (1-5) | Notes / Observations |
| ----------------- | ----------- | ------- | -------------- | -------------------- | -------------------- |
| 2026-07-30 | @student_a (Ngô Hoàng Phú) | #hỏi-đáp | Deadline CP4 khi nào? | 5 | Trả lời chính xác 23:59, kèm link bài gốc. |
| 2026-07-30 | @student_b (Đinh Quốc Việt) | #chung | Đăng ký học lại ở đâu? | 4 | Đúng thông tin nhưng phản hồi hơi chậm. |
| 2026-07-30 | @student_c (Nguyễn Thùy Trang) | #gõ-command | Hôm nay ăn gì? | 5 | Trả lời từ chối lịch sự theo quy tắc HAX G10. |
| 2026-07-31 | @student_d (Long) | #hỏi-đáp | Day 5 làm cá nhân hay nhóm? | 5 | Trả lời đúng hình thức nhóm, có trích dẫn tin nhắn gốc. |
| 2026-07-31 | @student_e (Trần Lê Quý Đăng) | #thông-báo | Các mốc thời gian chọn đề tài? | 5 | Trích xuất chuẩn xác từ ảnh banner (26/07, 30/07, 01/08). |

## 👥 Willing Users & CP5 Validation Interviews

### 1. User: Ngô Hoàng Phú (Mã HV: 2A202601244)
- **Q1: Bạn thấy Bot phản hồi có kịp thời không?**
  - *Trả lời*: "Lần thử mới này Bot phản hồi dưới 3s, rất nhanh so với trước."
- **Q2: Thông tin Bot cung cấp có đầy đủ và đáng tin cậy không?**
  - *Trả lời*: "Đầy đủ, có kèm link nhảy thẳng tới tin nhắn gốc của giảng viên nên rất yên tâm."
- **Q3: Bạn có đồng ý dùng Bot này hàng ngày thay vì lướt tìm tin nhắn không?**
  - *Trả lời*: "Đồng ý 100%, tiết kiệm rất nhiều thời gian."

### 2. User: Đinh Quốc Việt (Mã HV: 2A202601102)
- **Q1: Bạn thấy Bot phản hồi có kịp thời không?**
  - *Trả lời*: "Rất nhanh, dùng lệnh `/ask` câu trả lời hiện riêng tư rất tiện."
- **Q2: Thông tin Bot cung cấp có đầy đủ và đáng tin cậy không?**
  - *Trả lời*: "Bot không bịa đặt, câu nào không biết là báo ngay và tag TA hỗ trợ."
- **Q3: Bạn có đồng ý dùng Bot này hàng ngày không?**
  - *Trả lời*: "Có, đỡ phải đăng bài hỏi lặp đi lặp lại."

### 3. User: Nguyễn Thùy Trang (Mã HV: 2A202601294)
- **Q1: Bạn thấy Bot phản hồi có kịp thời không?**
  - *Trả lời*: "Phản hồi gần như lập tức khi tag Bot."
- **Q2: Thông tin Bot cung cấp có đầy đủ và đáng tin cậy không?**
  - *Trả lời*: "Đặc biệt ấn tượng với khả năng đọc chữ trong hình ảnh thông báo chọn đề tài."
- **Q3: Bạn có đồng ý dùng Bot này hàng ngày không?**
  - *Trả lời*: "Rất sẵn sàng."

## 📏 Score Metric Definitions
- **5 - Excellent**: Fully accurate answer, correctly cited sources, fast response time.
- **4 - Good**: Relevant and correct answer with minor formatting or minor delay.
- **3 - Acceptable**: Partially correct answer; missing secondary context or partial citation.
- **2 - Poor**: Inaccurate details or failed to fetch relevant context when present in DB.
- **1 - Unacceptable**: Hallucination, invalid citation, or violation of HAX rules.

