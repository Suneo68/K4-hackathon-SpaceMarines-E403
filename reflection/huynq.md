# Reflection cá nhân – Nghiêm Quốc Huy

## 1. Về dự án
Trong dự án này, tôi tham gia vào nhóm SpaceMarines để xây dựng sản phẩm AI phục vụ cộng đồng học tập: Kudo RAG Service. Đây là một trợ lý Discord có khả năng tra cứu thông tin từ các kênh thông báo, tài nguyên học tập và bài học, từ đó trả lời học viên dựa trên ngữ cảnh thực tế thay vì đoán mò hoặc bị ảo giác (hallucination).

Dự án này mang tinh thần cốt lõi của một kỳ hackathon: không chỉ làm ra một nguyên mẫu (prototype) chạy được, mà còn phải chứng minh sản phẩm giải quyết được vấn đề thật, có khả năng đánh giá độ chính xác và trình diễn được tính ứng dụng trong thực tế. Điều làm tôi thấy hứng thú nhất là dự án đòi hỏi sự phối hợp chặt chẽ giữa việc thu thập bằng chứng, kiểm định chất lượng gắt gao và cách kể câu chuyện sản phẩm qua buổi demo.

## 2. Vai trò của tôi trong dự án
Dựa trên phân công của nhóm, vai trò của tôi trải đều ở ba khía cạnh mang tính kiểm chứng và thuyết phục: Evidence, Validation, và Demo.

a) Xây dựng Evidence (Cùng Trần Văn Thi và Vũ Thế Lực)
Để chứng minh vấn đề của người dùng là có thật và giải pháp RAG là phù hợp, tôi đã tham gia vào việc thu thập và tổng hợp bằng chứng. Chúng tôi không thể chỉ dựa vào cảm tính, do đó công việc bao gồm:

Phân tích các nỗi đau (pain points) thực tế của học viên khi bị trôi tin nhắn, lỡ deadline hoặc không tìm thấy tài liệu.

Xây dựng các tình huống (use cases) đời thực để làm nền tảng cho bộ dữ liệu chuẩn (golden set).

Đảm bảo rằng quyết định làm sản phẩm được dựa trên các dữ kiện thực tế và nhu cầu cấp thiết, giúp nhóm định hình rõ ràng bài toán cần giải quyết.

b) Đảm nhiệm Validation (Cùng Vũ Thế Lực)
Một trợ lý AI học tập sẽ trở nên vô dụng, thậm chí gây hại nếu nó trả lời sai thông tin (như sai deadline, sai yêu cầu bài tập). Do đó, Validation là một khâu cực kỳ quan trọng:

Tôi tham gia đánh giá chất lượng câu trả lời của bot dựa trên các bộ test case đã thiết kế.

Kiểm tra chéo các ranh giới của bot: khi nào bot trả lời đúng dựa trên context, khi nào bot bắt đầu có dấu hiệu bịa đặt (hallucinate), và khi nào bot cần phải dũng cảm nói "Tôi không biết" hoặc tag chuyên gia.

Đảm bảo rằng các chỉ số và kết quả đầu ra đáp ứng được những tiêu chuẩn khắt khe đã đề ra trong Spec.

c) Thực hiện Demo (Cùng Vũ Thế Lực và Hoàng Tuấn Hưng)
Sản phẩm tốt đến đâu nếu không thể hiện được ra ngoài thì cũng không mang lại giá trị thuyết phục. Trong phần Demo:

Tôi cùng các thành viên chuẩn bị kịch bản trình diễn mượt mà nhất để ban giám khảo và người dùng thấy rõ "phép màu" của sản phẩm.

Chúng tôi chọn lọc những case tiêu biểu nhất (câu hỏi thông thường, câu hỏi lắt léo, câu hỏi ngoài luồng) để cho thấy khả năng xử lý thông minh và linh hoạt của Kudo RAG Service.

Trình bày trực quan luồng hoạt động của hệ thống từ khi user đặt câu hỏi đến khi nhận được câu trả lời chính xác, kèm theo trích dẫn nguồn.

## 3. Những gì tôi đã học được
Dự án này giúp tôi có cái nhìn toàn diện hơn về vòng đời phát triển của một AI Product, đặc biệt là:

a) Dữ liệu quyết định tất cả (Evidence-driven): Một giải pháp AI chỉ thực sự có giá trị khi nó được xây dựng trên nền tảng của vấn đề có thật. Bằng chứng rõ ràng giúp team không bị lạc lối.

b) Kiểm định AI không giống phần mềm truyền thống (Validation): Không giống như code đúng hoặc sai (1 hoặc 0), đầu ra của LLM rất khó đoán. Việc xây dựng cơ chế đánh giá (validation) đòi hỏi sự kiên nhẫn, góc nhìn bao quát và tư duy phòng ngừa rủi ro.

c)Nghệ thuật trình diễn sản phẩm (Demo): Cách chúng ta kể câu chuyện của sản phẩm trong lúc demo quyết định 50% sự thành công. Một kịch bản demo tốt phải xoáy sâu vào nỗi đau của người dùng và cách sản phẩm chữa lành nỗi đau đó.

## 4. Thách thức trong quá trình làm việc
Tìm sự cân bằng trong Validation: Rất khó để định lượng thế nào là một câu trả lời "đủ tốt". Đôi khi bot trả lời đúng ý nhưng sai văn phong, hoặc an toàn quá mức dẫn đến từ chối trả lời những câu nó hoàn toàn có thể làm được.

Áp lực lúc Demo: Demo các ứng dụng liên quan đến LLM luôn tiềm ẩn rủi ro "vỡ kế hoạch" vì model có thể phản hồi không như ý muốn tại thời điểm live. Chúng tôi đã phải chuẩn bị rất kỹ các phương án dự phòng.

Liên kết giữa Evidence và Validation: Đảm bảo rằng những test case dùng để validate thực sự phản ánh đúng những bằng chứng (evidence) về nhu cầu người dùng đã thu thập ban đầu.

## 5. Kết quả và góc nhìn cá nhân
Nhìn lại hành trình này, tôi thấy bản thân trưởng thành hơn rất nhiều trong tư duy làm sản phẩm. Tôi nhận ra rằng: Code xong một tính năng không có nghĩa là xong việc. Việc chúng ta chứng minh được nó cần thiết (Evidence), đảm bảo nó hoạt động đúng đắn và an toàn (Validation), và truyền tải được giá trị đó đến người khác (Demo) mới là những mảnh ghép hoàn thiện một sản phẩm xuất sắc.

Dự án không chỉ là nơi áp dụng công nghệ RAG, mà còn là nơi rèn luyện sự tỉ mỉ, khả năng làm việc nhóm và tư duy hướng tới người dùng cuối.

6. Kết luận
Kudo RAG Service mang lại cho tôi những bài học thực chiến sâu sắc về cách vận hành của một AI project. Đảm nhận các khâu từ đầu vào (Evidence), kiểm soát chất lượng (Validation) đến đầu ra (Demo), tôi hiểu được tầm quan trọng của việc duy trì tính nhất quán của sản phẩm.

Đây là một cột mốc quan trọng, giúp tôi tự tin hơn không chỉ trong việc phát triển hệ thống mà còn trong việc chứng minh, bảo vệ và lan tỏa giá trị của các giải pháp công nghệ đến với cộng đồng.