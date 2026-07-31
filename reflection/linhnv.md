# Reflection cá nhân – Linh NV

## 1. Về dự án

Trong dự án này, tôi tham gia vào nhóm SpaceMarines để xây dựng một sản phẩm AI phục vụ cộng đồng học tập: Kudo RAG Service, một trợ lý Discord có khả năng tra cứu thông tin từ các kênh thông báo, tài nguyên học tập và bài học, rồi trả lời học viên dựa trên ngữ cảnh có thật thay vì đoán mò. Đây là một dự án rất phù hợp với tinh thần của hackathon: không chỉ xây dựng prototype, mà còn phải chứng minh rằng sản phẩm có khả năng hoạt động thực tế, giải quyết được pain point của học viên và mang lại trải nghiệm mượt mà.

Điều làm tôi thấy hứng thú nhất là việc được trực tiếp "nhào nặn" hệ thống từ những dòng code và prompt đầu tiên, biến một spec trên giấy thành một con Bot có thể tương tác và phản hồi chính xác trên Discord.

## 2. Vai trò của tôi trong dự án

Vai trò của tôi chủ yếu tập trung vào phần thực thi kỹ thuật, cụ thể là: **Prompt Engineering** và **Coding (Lập trình hệ thống)**.

### a) Prompt Engineering
Để RAG (Retrieval-Augmented Generation) hoạt động hiệu quả, việc có được các chunks dữ liệu tốt mới chỉ là một nửa chặng đường. Nửa còn lại là làm sao để LLM hiểu và trả lời đúng trọng tâm. Tôi đã tập trung vào việc thiết kế và tối ưu các prompt cho Gemini 2.5 Flash:
- Thiết lập System Prompt chặt chẽ để Bot luôn giữ thái độ lịch sự, chuyên nghiệp của một "Kudo Assistant".
- Xây dựng kịch bản Fallback: Đảm bảo Bot sẽ thẳng thắn thừa nhận "không biết" khi không có dữ liệu, thay vì bị ảo giác (hallucination) và bịa ra thông tin.
- Thiết kế luồng trích xuất (Route to Expert): Dùng prompt để Bot có khả năng phân loại chủ đề câu hỏi (Ví dụ: Python, Kafka, Git) và tag đúng chuyên gia hỗ trợ khi cần thiết.

### b) Coding & Tích hợp hệ thống
Việc kết nối tất cả các thành phần lại với nhau đòi hỏi rất nhiều công sức code và debug. Những công việc tôi đã đảm nhiệm bao gồm:
- **Xây dựng Bot Discord:** Tích hợp thư viện `discord.py`, xử lý các sự kiện `on_message` và tạo các Slash Commands tiện ích (`/ask`, `/trace`, `/stats`).
- **Xây dựng luồng RAG Pipeline:** Code logic kết nối giữa Discord, ChromaDB (Vector Store) và Gemini API. Đảm bảo việc query và nạp dữ liệu (ingestion) diễn ra mượt mà, tối ưu hóa các hàm đồng bộ và bất đồng bộ (async/await).
- **Tối ưu trải nghiệm UI (Discord Embeds):** Chăm chút từng dòng code hiển thị để Bot trả về các thẻ màu UI chuyên nghiệp (Xanh lá thành công, Vàng cảnh báo, Tím phân tích), tự động chunking text nếu vượt quá giới hạn 4000 ký tự của Discord để không làm vỡ layout.

## 3. Những gì tôi đã học được

Dự án này giúp tôi nâng cao đáng kể kỹ năng thực chiến với AI và lập trình hệ thống:

1. **Sức mạnh của Prompt Engineering:** Một câu lệnh sai khác một chữ cũng có thể thay đổi hoàn toàn hành vi của LLM. Việc thiết kế prompt không chỉ là "ra lệnh", mà là thiết lập một bộ quy tắc (guardrails) an toàn cho AI.
2. **Kỹ năng xử lý luồng bất đồng bộ (Async/Await):** Làm việc với Discord API và LLM API đòi hỏi hệ thống không được block các request khác. Tôi đã học được cách tối ưu hiệu năng để Bot phản hồi nhanh, không bị crash khi có nhiều người dùng hỏi cùng lúc.
3. **Giá trị của việc làm UI/UX trên nền tảng text:** Dù chỉ là chatbot trên Discord, nhưng việc sử dụng Markdown, Embeds, và sắp xếp bố cục thông tin (hiển thị source, thời gian phản hồi) lại quyết định rất lớn đến cảm nhận chuyên nghiệp của sản phẩm.

## 4. Thách thức trong quá trình làm việc

Trong quá trình thực hiện, tôi gặp không ít khó khăn kỹ thuật:
- **Xử lý giới hạn của Discord:** Ban đầu, những câu trả lời dài bị Discord cắt ngang thô bạo (do giới hạn 2000 ký tự của plain text) làm hỏng toàn bộ định dạng. Tôi phải debug và tìm ra giải pháp dùng vòng lặp chia nhỏ text nhét vào các Discord Embeds (chứa được 4000 ký tự) để giữ nguyên vẹn Markdown, cũng như đồng bộ hóa các dải màu (Color UI) cho từng bối cảnh trả lời.
- **Tối ưu độ trễ (Latency):** Việc nhét RAG flow vào một luồng request tốn khá nhiều thời gian. Phải xử lý logic hiển thị "typing" để người dùng không cảm thấy bot bị treo.
- **Xử lý Hallucination:** Bot ban đầu rất hay "tỏ ra thông minh" và bịa câu trả lời khi thiếu context. Tôi đã phải lặp đi lặp lại việc tuning prompt rất nhiều lần mới đạt được mức độ an toàn (Grounded RAG) như hiện tại.

## 5. Kết quả và góc nhìn cá nhân

Nhìn thấy sản phẩm chạy thực tế, xử lý trơn tru các câu hỏi hóc búa, và hiển thị giao diện Embed lộng lẫy, tôi cảm thấy cực kỳ tự hào. Sản phẩm không chỉ là một cái "vỏ bọc" AI mà thực sự giải quyết bài toán thông tin một cách có hệ thống.

Về góc nhìn cá nhân, tôi nhận ra rằng một "AI Engineer" giỏi trong thời điểm hiện tại không nhất thiết phải là người train ra một model mới, mà là người biết kết hợp sức mạnh của các model hiện có (LLM) với tư duy lập trình hệ thống (Software Engineering) để tạo ra một ứng dụng hoàn chỉnh, có UI/UX tốt và chạy ổn định.

## 6. Kết luận

Dự án Hackathon này là một bước đệm tuyệt vời giúp tôi ráp nối các mảnh ghép kiến thức từ lập trình ứng dụng đến AI/RAG. Với vai trò Prompting và Code, tôi đã hiểu sâu sắc hơn về cách mà một AI Product vận hành "dưới mui xe" (under the hood). Việc đồng hành cùng nhóm SpaceMarines để đi từ ý tưởng, spec, đến một bản demo thực chiến chạy mượt mà trên Discord là một trải nghiệm cực kỳ giá trị cho con đường phát triển sự nghiệp kỹ sư phần mềm AI của tôi sau này.