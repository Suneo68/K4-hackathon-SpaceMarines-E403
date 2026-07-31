# Worksheet JTBD đầy đủ (tham khảo sâu — bản nhẹ nằm trong 02-guide.md §1)


# Worksheet B1 — Chân dung user & Jobs To Be Done

**Nhóm:** SpaceMarines · **Hướng:** [ ] A — VLearn [X] B — Trợ lý Học viên [ ] C — Làn mở

> Quy tắc xuyên suốt: **không rõ job thì đừng bàn feature.**
> File này điền trực tiếp và nộp kèm trong repo — nó là phần đầu vào của Phiếu nghiệm thu CP1.

## Cách dùng Strategyn Playbook (KHÔNG đọc hết 48 trang)

## 1. Chọn job executor *(5')*

**Job executor của nhóm:** Học viên đang theo học (cần tìm lại tài liệu, thông báo, vắng buổi, ôn tập trước quiz, hỏi bài khi kẹt lab/bài tập) / Đội ngũ TA / Lab Coach: Người phải giải đáp thắc mắc và duy trì vận hành lớp học 24/7 · **Vì sao là người này:** Học viên đôi khi không được cung cấp thông tin nhanh chóng và chính xác theo realtime, những thông tin đã được mentor hay TA xác nhận tại phần hỏi đáp nhưng chưa kịp cập nhật lên bảng thông tin cho Bot.

## 2. Vẽ workflow thật của họ *(10')*

| Chặng | Họ đang cố làm gì? | Hôm nay họ dùng gì? (tua video / hỏi bạn / hỏi tutor / ChatGPT riêng / bỏ qua) | Kẹt ở đâu? | Mức đau |
|---|---|---|---|---|
| Trước buổi | [Define] Xác định mục tiêu: Hôm nay học môn gì, topic nào.[Locate] Tìm kiếm: Lục lọi link Zoom/Meet, slide bài giảng.[Prepare] Chuẩn bị: Tải tài liệu, mở sẵn Notion/Word, bật các phần mềm cần thiết. | - Zalo group lớp / Discord. - Hệ thống LMS | - Link học và tài liệu bị rải rác nhiều nơi, trôi tin nhắn. - Giảng viên gửi tài liệu quá sát giờ, không kịp đọc trước. | M |
| Trong buổi | [Confirm] Xác nhận: Check mic, cam, màn hình share (Thường N/A với lớp offline). [Execute] Thực thi: Nghe giảng, ghi chép, cố gắng hiểu các concept khó. [Monitor] Giám sát: Nhận ra bản thân đang không hiểu phần nào để đặt câu hỏi. | - Gõ máy tính / Viết sổ tay.- Chụp màn hình slide.- Nhắn tin hỏi bạn bè.- Dùng ChatGPT riêng để tra khái niệm nhanh. | Có những thông tin không kịp cập nhật để biết | H |
| Ngay sau buổi | [Modify] Điều chỉnh: Bổ sung những đoạn ghi chép bị thiếu hoặc sai sót lúc học. [Conclude] Kết thúc: Lưu trữ file, gom tài liệu, nộp bài điểm danh và đóng máy. | - Xin record từ giảng viên. - Hỏi mượn vở/note của bạn học giỏi.| - Mệt mỏi, lười tổng hợp ngay nên thường bỏ qua bước này. - Phải chờ rất lâu mới có video record để xem lại phần bị lỡ. | M |
| Khi ôn lại | [Locate] Tìm kiếm (Vòng lặp): Bới lại ghi chép cũ để làm bài tập/ôn thi. [Execute] Thực thi (Vòng lặp): Học thuộc, xâu chuỗi kiến thức, thực hành. | - Tua video record bài giảng. - Đọc lại slide và đống ghi chú rải rác. - Hỏi Tutor / Mentor. - Dùng AI tóm tắt tài liệu.  | hông tóm tắt được thông tin cũng như cập nhật thông tin từ các cuộc thảo luận bài trên lớp | H |

**Hai chỗ đau nhất trong workflow:** #1 Không cập nhật kịp thời thông tin từ ban tổ chức · #2 Không nắm rõ được thông tin từ các cuộc thảo luận.
**Bằng chứng ban đầu cho 2 chỗ này** (từ chatlog/Discord/tự quan sát — sẽ đào sâu ở Bước 2): Thông tin đã được Mentor phản hồi trong kênh chat nhưng BOT Kute lại chưa kịp cập nhật thông tin này khiến dẫn đến BOT Kute trả lời không biết, không có thông tin.

## 3. Viết core JTBD *(7')*

**Core JTBD bản nháp:** Đưa ra thông tin nhanh nhất cho học viên 1 cách nhanh nhất.
**Từ solution lỡ nhét vào (gạch bỏ):** thu thập thông tin được cung cấp chính thức từ TA hay Mentor(việc chờ đợi thông tin này gây trễ trong việc phản hồi)
**Core JTBD bản chốt:** Tìm kiếm và tổng hợp thông tin chính xác từ các thông báo, tài nguyên bài học và thảo luận lớp học trên Discord trong thời gian ngắn nhất mà không bị trôi tin nhắn

## 4. Ba job stories *(7')*

Format: `When [trigger], I want to [motivation], so I can [outcome].`

| # | When | I want to | So I can | Story này cho thấy gì |
|---|---|---|---|---|
| JS1 | Khi tôi mở Discord vào sáng thứ Hai để xem yêu cầu bài tập nhưng kênh chat bị trôi hàng trăm tin nhắn tán gẫu từ đêm qua | Tôi muốn lập tức trích xuất được những thông báo chính thức và link bài tập do giảng viên gửi |  Nắm bắt ngay deadline và bắt tay vào làm bài mà không phải lướt đọc mỏi mắt để tự chắt lọc thông tin.| Nỗi đau về "Noise vs. Signal" (Nhiễu thông tin): Cần tách biệt rõ ràng giữa luồng chat giao tiếp xã hội và luồng thông báo/nhiệm vụ học tập.|
| JS2 | Khi tôi đang ôn thi và nhớ ra một diagram giải thích rất hay mà mentor từng gửi trong một thread thảo luận cách đây 3 tuần | Tôi muốn tìm lại chính xác file/hình ảnh đó chỉ bằng một vài từ khóa nhớ mang máng (ví dụ: "ảnh sơ đồ db") | Tải được tài liệu để ôn tập ngay lập tức thay vì phải cuộn chuột tìm lại một cách vô vọng hoặc ngại ngùng nhắn hỏi lại mentor. | Nỗi đau về "Retrieval" (Truy xuất tài nguyên): Cách Discord lưu trữ file trong luồng chat rất tệ cho việc học. Cần một nơi gom nhóm tài nguyên tập trung hoặc công cụ search mạnh mẽ hơn. |
| JS3 | Khi tôi bị kẹt (bug) ở một bài tập khó và biết chắc chắn hôm qua đã có bạn hỏi lỗi y hệt nhưng đoạn giải đáp đã bị trôi mất | Tôi muốn xem lại trọn vẹn mạch hỏi - đáp (Q&A) đã được chốt (resolved) cho vấn đề đó một cách mạch lạc | Tự sửa được lỗi của mình và code tiếp ngay lập tức thay vì phải đặt lại câu hỏi y hệt và chờ mentor online trả lời lại từ đầu. | Nỗi đau về "Lost Knowledge" (Lãng phí tri thức tập thể): Các thảo luận giá trị bị biến mất theo thời gian thực. Cần tính năng tự động tổng hợp/lưu trữ các Q&A hay thành FAQ (có thể ứng dụng AI để tóm tắt luồng chat). |


## 5. Current alternatives *(5')*

Đối thủ = bất kỳ thứ gì user đang "thuê" để làm job: tua video, hỏi bạn cùng nhóm, hỏi tutor hiện tại, ChatGPT/Claude riêng, Google, tự bỏ qua.

| Alternative | Làm tốt gì? | Fail ở đâu? | Vì sao user chưa bỏ nó? |
|---|---|---|---|
|Tự lướt/cuộn tìm tin nhắn cũ trong kênh chung |Nếu tìm được thì thông tin chắc chắn chuẩn xác 100% (nguồn gốc). Không phải phụ thuộc ai. |Tốn rất nhiều thời gian. Dễ nản vì tin nhắn thông báo bị hàng trăm tin nhắn tán gẫu đè lên. |Bản năng đầu tiên của người dùng khi cần tìm đồ, và do Discord có thanh search (dù không hiệu quả). |
|Hỏi bạn học khác (nhắn lên #💬-chung) |Nhanh, tiện tay, thường được phản hồi ngay vì lúc nào cũng có người online. Tâm lý thoải mái. |Thông tin mang tính "đoán mò", truyền miệng, không có căn cứ, dễ dẫn đến làm sai quy định và mất điểm. |Thói quen giao tiếp xã hội, tiện tay gõ luôn vào kênh chung vì ngại/sợ hỏi trực tiếp TA. |
|Hỏi trực tiếp TA / Tutor (Tag tên hoặc DM)|Giải đáp uy tín, chính xác, xử lý được cả những case đặc biệt/khó.|Phụ thuộc vào thời gian rảnh của TA (chờ lâu). Về phía TA: Tốn thời gian vì phải trả lời đi trả lời lại các câu vặt vãnh.-|Đây là chốt chặn an toàn nhất. Khi hỏi bạn không được và tự tìm không xong thì buộc phải hỏi TA.|
|Dùng ChatGPT / Claude cá nhân|Trả lời ngay lập tức, hỗ trợ giải thích kiến thức bài học rất tốt.-|"Mù" thông tin nội bộ của lớp (ví dụ: không biết "Hạn nộp CP4 khi nào", "Link slide ở đâu").|Vẫn là công cụ đắc lực để học bài/làm lab, dù vô dụng trong việc tìm kiếm thông báo hành chính của lớp.|

**Nếu sản phẩm nhóm không ra đời, user sẽ tiếp tục:** cập nhật chậm thông tin dù thông tin đã được Mentor hay TA xác nhận ở kênh chat.
## 6. AI leverage point *(nộp vào CP1)*

- Đừng nhét AI vì "có AI nghe hay". Nếu chỗ đau nhất không phải chỗ AI giải tốt — ghi thẳng ra và chọn lại.
- Với hướng **tối ưu tính năng có sẵn**: leverage point = chỗ tính năng hiện tại đang fail job (kèm bằng chứng từ chatlog).

**AI nên vào bước nào của workflow, vai trò gì:** Tìm kiếm/truy xuất thông tin nội bộ trong Discord và trả lời câu hỏi lớp học trên Discord. / Trợ lý RAG — tự động ingest và index thông báo, tài nguyên, thảo luận; trả lời câu hỏi bằng cách lấy chính xác context từ Discord và trích dẫn nguồn gốc.
**Vì sao không phải bước khác:** Vì dự án hiện tại chọn hướng Tối ưu tính năng có sẵn: cải thiện khả năng tìm/gom thông tin nội bộ, không phải xây AI tutor giải thích học thuật toàn bộ. / Người dùng đang có ChatGPT/Claude để hiểu khái niệm và TA để hỏi case khó, nhưng đang fail ngay ở chỗ: thông tin nội bộ trên Discord bị trôi, tìm search kém, không biết link/announcement nào là chính thức.
**Product hypothesis** (công thức):Nếu giúp học viên đang dùng Discord làm job: tìm kiếm và tổng hợp thông tin chính xác từ thông báo, tài nguyên và thảo luận lớp học tốt hơn ở bước truy vấn/QA nội bộ, bằng AI leverage: real-time RAG trên Discord với grounding và citation, họ sẽ chuyển từ đang tự cuộn chat/hỏi TA/dùng ChatGPT ngoài hệ thống sang dùng Kudo Assistant, vì nhanh hơn, ít phải đọc lướt, và câu trả lời có nguồn nội bộ rõ ràng.
> ___________

**Assumption nguy hiểm nhất nếu nhóm đang sai** (sẽ kiểm bằng evidence + vòng validation CP5): Nhóm đang giả định rằng pain lớn nhất là retrieval/knowledge surfacing trên Discord, chứ không phải là pain lớn nhất là học thiếu hiểu biết kiến thức chuyên sâu.
