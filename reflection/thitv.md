# Reflection cá nhân – Trần Văn Thi

## 1. Về dự án

Trong dự án này, tôi tham gia vào nhóm SpaceMarines để xây dựng một sản phẩm AI phục vụ cộng đồng học tập: Kudo RAG Service, một trợ lý Discord có khả năng tra cứu thông tin từ các kênh thông báo, tài nguyên học tập và bài học, rồi trả lời học viên dựa trên ngữ cảnh có thật thay vì đoán mò. Đây là một dự án rất phù hợp với tinh thần của hackathon: không chỉ xây dựng prototype, mà còn phải chứng minh rằng sản phẩm có ý nghĩa, có căn cứ và có thể giải quyết được một vấn đề thực tế.

Điều làm tôi thấy hứng thú nhất là dự án này không dừng ở việc “viết code”, mà buộc mình phải suy nghĩ như một người làm sản phẩm: hiểu người dùng, xác định pain point, lựa chọn giải pháp phù hợp và trình bày bằng chứng rõ ràng.

## 2. Vai trò của tôi trong dự án

Vai trò của tôi chủ yếu tập trung vào hai phần: viết spec và xây dựng evidence.

### a) Viết spec
Tôi tham gia xây dựng phần spec cho sản phẩm, từ việc định nghĩa vấn đề, chuyển hóa nhu cầu người dùng thành một problem statement rõ ràng, đến thiết kế phạm vi sản phẩm, các non-goals, trải nghiệm người dùng và các kịch bản kiểm thử. Đây là phần rất quan trọng vì nó giúp cả nhóm có chung một định hướng và tránh bị lan sang những thứ không cần thiết.

Một điểm tôi thấy mình học được nhiều là cách viết một spec không chỉ để “đẹp” mà phải đủ chặt chẽ để người khác có thể hiểu được mục tiêu, giới hạn và cách đánh giá sản phẩm. Trong quá trình này, tôi đã cố gắng làm rõ ba điều:

- Sản phẩm giải quyết vấn đề gì?
- Ai là người dùng chính?
- Khi nào bot nên trả lời, khi nào nên từ chối hoặc chuyển cho con người?

### b) Xây dựng evidence
Phần evidence là phần tôi thấy mình học được nhiều nhất. Vì dự án này đòi hỏi không chỉ “có ý tưởng”, mà phải có bằng chứng để bảo vệ ý tưởng. Vì vậy, tôi đã cùng nhóm tập hợp và sử dụng các dữ kiện như:

- Kết quả khảo sát về trải nghiệm học viên khi tìm kiếm thông báo và deadline.
- Các quote thực tế từ học viên về việc họ thường mất thời gian, bị trôi tin nhắn hoặc phải hỏi lại nhiều lần.
- Các trường hợp thực tế trong đời sống lớp học để chứng minh rằng nhu cầu tìm kiếm thông tin nhanh và chính xác là rất lớn.
- Các case test trong golden set để thể hiện sản phẩm có thể xử lý được các tình huống khác nhau, kể cả những trường hợp mơ hồ, không có dữ liệu hoặc có rủi ro cao.

Nhờ có evidence như vậy, quyết định chọn giải pháp RAG không còn là một suy đoán mà trở thành một lựa chọn có căn cứ.

## 3. Những gì tôi đã học được

Dự án này giúp tôi hiểu rõ hơn về cách làm việc trong một môi trường AI product, đặc biệt là ba thứ sau:

1. Tư duy sản phẩm quan trọng hơn nhiều so với chỉ tập trung vào kỹ thuật.
   - Một ý tưởng AI có thể rất hay, nhưng nếu không gắn với nhu cầu thật của người dùng thì sẽ không có giá trị.

2. Evidence là yếu tố quyết định.
   - Khi trình bày một giải pháp, việc có dữ liệu và ví dụ cụ thể làm cho ý tưởng trở nên đáng tin cậy và dễ thuyết phục hơn.

3. Một sản phẩm AI cần có giới hạn rõ ràng.
   - Điều này rất quan trọng vì AI dễ bị ảo giác. Trong dự án này, chúng tôi đã chọn cách thiết kế bot chỉ trả lời khi có ngữ cảnh đủ tin cậy, còn khi không chắc thì chuyển cho chuyên gia hoặc từ chối trả lời.

## 4. Thách thức trong quá trình làm việc

Trong quá trình thực hiện, tôi cũng gặp một số thách thức nhất định:

- Cần chuyển hóa một vấn đề rất “mơ hồ” thành một định nghĩa sản phẩm rõ ràng.
- Cần balance giữa tính “thực tế” và tính “đầy đủ” trong spec.
- Cần trình bày yếu tố bằng chứng mà vẫn giữ cho nội dung vừa ngắn gọn vừa có sức thuyết phục.

Tuy nhiên, chính những thách thức này lại giúp tôi trưởng thành hơn. Tôi hiểu rằng một sản phẩm AI tốt không chỉ nằm ở việc “model chạy được”, mà còn nằm ở cách chúng ta xây dựng nền tảng logic, giới hạn và độ tin cậy cho sản phẩm đó.

## 5. Kết quả và góc nhìn cá nhân

Sau khi tham gia dự án, tôi thấy mình đã tiến bộ ở nhiều mặt. Không chỉ hiểu hơn về cách viết spec và trình bày evidence, mà còn biết cách nhìn một vấn đề bằng góc độ người dùng, bởi vì sản phẩm AI thật sự chỉ có giá trị khi nó giải quyết được nỗi đau thật của người dùng.

Nếu nhìn lại toàn bộ quá trình, tôi thấy đây là một trải nghiệm rất đáng giá. Tôi không chỉ học cách làm việc nhóm, mà còn học được cách biến một ý tưởng ban đầu thành một sản phẩm có cấu trúc, có căn cứ và có khả năng triển khai. Đây là một bài học quan trọng cho tôi trong hành trình trở thành một người làm sản phẩm AI, chứ không chỉ là người dùng AI.

## 6. Kết luận

Dự án này đã cho tôi một trải nghiệm rất thực tế về cách xây dựng một sản phẩm AI từ đầu đến cuối: từ xác định vấn đề, viết spec, thu thập evidence, đến đưa ra giải pháp và kiểm thử. Với vai trò chính trong phần spec và evidence, tôi nhận ra rằng một sản phẩm tốt không chỉ cần “chạy được”, mà còn cần có nền tảng logic vững chắc và bằng chứng để chứng minh rằng nó thực sự giải quyết được vấn đề mà người dùng đang gặp phải.

Đây là một dự án có ý nghĩa với tôi vì nó giúp tôi nhìn thấy rõ hơn về vai trò của người làm spec và người làm evidence trong một dự án AI: họ không chỉ “viết nội dung”, mà còn là những người tạo ra nền tảng cho sự tin cậy, tính hợp lý và giá trị thực tế của sản phẩm.
