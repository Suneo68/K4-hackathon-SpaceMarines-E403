# Template AI Spec *(spec.md — commit trước 23:59 N1 · quality bar chốt từ thời điểm nộp)*

```markdown
# AI SPEC — [Trợ lý học viên Kudo] · Nhóm [SpaceMarines] · Zone [A]
Hướng: [ ] A — VLearn  [X] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [X] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job
- Job executor + workflow (đính kèm worksheet JTBD / ảnh sơ đồ): tham-khao\worksheet-jtbd-day-du.md
- Core JTBD (không tên sản phẩm/AI trong câu): Tìm kiếm và tổng hợp thông tin chính xác từ các thông báo, tài nguyên bài học và thảo luận lớp học trên Discord trong thời gian ngắn nhất mà không bị trôi tin nhắn
- Problem statement (KHÔNG chữ AI): Học viên mất quá nhiều thời gian để lướt tìm các thông báo, deadline và tài liệu quan trọng bị trôi vùi trong hàng trăm tin nhắn giao tiếp rác trên kênh chung. Hệ quả là họ phải hỏi đi hỏi lại các câu hỏi giống nhau, hoặc dựa vào thông tin truyền miệng thiếu kiểm chứng từ bạn học, dẫn đến việc lỡ hạn nộp bài, làm sai quy định và tạo khối lượng công việc trả lời lặp lại khổng lồ cho đội ngũ trợ giảng (TA).
- Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):
  - Số liệu mining / kết quả khảo sát (n = ?, % xác nhận): n = 8, 100% xác nhận sẽ dùng nếu đảm bảo được tính năng.
  - ≥5 quote/ví dụ nguyên văn + nguồn(Nguồn khảo sát đánh giá Kute hiện tại: https://docs.google.com/forms/d/e/1FAIpQLSfvj210rAFWLXAs16ejDg4thu5AvxOI9qurGdoAxTGSbUGD8w/viewform?usp=sharing&ouid=102773071886227651922):
|Họ tên|Mã HV|Bạn thấy trợ lý Kute có hỗ trợ kịp thời vấn đề của bạn không?| Trợ lý Kute có hỗ trợ đủ thông tin cho câu hỏi của bạn không?|Nếu Trợ lý Kute có thể hỗ trợ kịp thời "REALTIME" những thông tin mới nhất cho bạn thì bạn có đồng ý không ?|

|Ngô Hoàng Phú|2A202601244|Có nhưng chưa kịp thời| Không |Có|
|Đinh Quốc Việt|2A2026*****|Có nhưng chưa kịp thời| Trả lời không đúng ý |Có|
|Nguyễn Thuỳ Trang|2A202601294|Có | Mơ hồ |Có|
|Long|2A202601744|Có| Có + Mơ hồ |Có|
|Trần Lê Quý Đăng|2A202601408|Có + không | Không + Mơ hồ |Có|


## §2. Impact & quyết định chọn
- Bảng impact ≥3 ứng viên (bao nhiêu người · tần suất · tốn gì mỗi lần · khả thi):
|Ứng viên|Bao nhiêu người|Tốn gì mỗi lần? | Tần suất |Khả thi / Đánh giá|
|---|---|--- |--- |----|
|ƯV1: Tổng hợp FAQ tĩnh bằng tay (TA tự gom các câu hỏi/thông báo bỏ vào 1 link Notion/Sheet chung).|Toàn bộ học viên + Đội ngũ TA.|- Học viên: Tốn công tự mở link, tự search (Ctrl+F). - TA: Tốn rất nhiều sức (Manual work) để cập nhật liên tục. | Mỗi ngày. |Khả thi cao, nhưng giải quyết không triệt để. Đòi hỏi con người duy trì.|
|ƯV2: Chatbot tạo sinh tự do (Generative LLM) (Cho bot tự động đọc Discord và trả lời mọi thứ, không kiểm soát nguồn).|Toàn bộ học viên.|- Học viên: Rủi ro "Cost-of-Error" cực cao (sai deadline, sai format bài nộp). - Hệ thống: Tốn token API. | Vài lần / ngày / người. |Khả thi kỹ thuật cao, nhưng độ tin cậy thấp (ảo giác/hallucination)|
|ƯV3: Bot truy xuất dữ liệu có điều kiện (RAG + Fallback) (Trả lời kèm link trích dẫn từ Vector DB; chuyển cho TA nếu không có dữ liệu).|Toàn bộ học viên.|- Học viên: 3-5 giây chờ đợi bot xử lý ngữ nghĩa. - Hệ thống: API cost. | Vài lần / ngày / người. |Khả thi cực cao nhờ kết hợp semantic search (qua Vector DB) với quy trình hỗ trợ của con người.|
- Ứng viên ĐÃ LOẠI + vì sao: UV1 + UV2 bị loại vì gây tốn rất nhiều thời gian, không giải quyết "nỗi đau" lười tìm kiếm của người học + môi trường học thuật yêu cầu kiến thức chuẩn và có nguồn rõ ràng.
- Ứng viên CHỌN + vì sao (bằng số): UV3 được chọn vì giải quyết được vấn đề việc TA phải trả lời các câu hỏi lặp lại liên tục từ học viên/ giảm thông tim sai lệch nhờ cơ chế fallback(nếu ko tìm thấy câu trả lời sẽ gợi ý đến cho TA - giúp giảm công việc của TA)/ Giảm thời gian truy xuất thông tin từ các post/ thảo luận mà vẫn đảm bảo độ chính xác của thông tin.
## §3. Giải pháp tương tự đã nghiên cứu
- [Sản phẩm 1]: flow / đáng học / đáng né / mình khác gì
- [Sản phẩm 1: Tính năng Auto-responder của các Discord Bot truyền thống (MEE6, Dyno)]: flow: Admin (TA) cài đặt sẵn các cú pháp cứng (ví dụ: !deadline_cp4, !slide). Học viên gõ đúng chính xác cú pháp đó vào khung chat -> Bot tự động trả về một đoạn text đã được lập trình sẵn. / đáng học: Phản hồi cực kỳ nhanh (độ trễ gần như bằng 0). Tích hợp sẵn ngay trong nền tảng Discord, học viên không phải chuyển app. / đáng né: Quá cứng nhắc. Nếu học viên hỏi tự nhiên "Mọi người ơi cho mình hỏi hạn nộp bài CP4 là khi nào vậy?" thì bot sẽ "mù" và không trả lời được do không đúng keyword. TA vẫn phải mất công cập nhật thủ công (manual) đáp án cho bot mỗi khi có deadline mới. / mình khác gì: Hệ thống của mình dùng Vector DB để hiểu ngữ nghĩa (semantic) thay vì keyword. Học viên có thể hỏi bằng ngôn ngữ tự nhiên. Hơn nữa, dữ liệu của bot mình là động (dynamic), tự động cập nhật từ các kênh thông báo chính thức chứ không bắt TA phải tự gõ lại đáp án mỗi ngày.
- [Sản phẩm 2: Hệ thống Chatbot FAQ theo kịch bản (Rule-based Chatbot trên nền tảng LMS/Dialogflow cũ)]: flow: Học viên bấm vào icon chat góc màn hình $\rightarrow$ Hiện ra một menu các nút bấm (Ví dụ: [1. Lịch học] [2. Deadline] [3. Tài liệu]) ->  Học viên bấm chọn theo luồng cây quyết định (decision tree) cho đến khi ra được câu trả lời. Nếu bí, sẽ có nút "Gặp nhân viên hỗ trợ". / đáng học: Cơ chế "Fallback" (chuyển cho con người) hoạt động rất rành mạch. Tránh được việc bot cung cấp thông tin sai lệch. / đáng né: Phải rời khỏi không gian học tập/thảo luận chung (Discord) để vào một hệ thống khác. Luồng menu nút bấm quá rườm rà, học viên thà quay lại chat group hỏi bạn bè cho nhanh thay vì ngồi bấm qua 5-6 lớp menu. Khối lượng kiến thức bị giới hạn hoàn toàn trong kịch bản tĩnh được soạn sẵn. / mình khác gì: Đưa thẳng giải pháp vào môi trường người dùng đang hoạt động (kênh #🙋-hỏi-đáp trên Discord). Loại bỏ hoàn toàn sự rườm rà của nút bấm menu bằng truy vấn trực tiếp bằng câu hỏi. Đặc biệt, bot của mình có khả năng trích dẫn link nguồn (citation) về tin nhắn gốc của giảng viên, tạo ra sự tin cậy tuyệt đối (Grounding) mà các bot FAQ cũ không làm được.

## §4. Thiết kế
- Lát cắt MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả): Học viên đặt câu hỏi ở kênh `#🙋-hỏi-đáp` → AI tự động tra cứu dữ liệu mới nhất từ các kênh thông báo/bài học → Trả lời chính xác ngay lập tức kèm Link trích dẫn dẫn thẳng tới tin nhắn gốc.
- Non-goals (≥3 thứ KHÔNG build):
  - Không build một chatbot học thuật tổng quát để giải thích kiến thức hoặc giải bài tập rộng rãi.
  - Không build hệ thống trả lời rule-based keyword cứng nhắc như menu nút hoặc command template.
  - Không build một app/web UI mới ngoài Discord; tương tác chính là trong kênh Discord hiện tại.
  - Không auto-đăng thông báo hay thay thế TA hoàn toàn; bot chỉ hỗ trợ truy vấn và escalation khi không chắc.
- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [X] Working — phần nào mock, phần nào thật: Discord bot và vector search/RAG thật; phần fallback TA có thể là quy trình mock trong bản demo nếu cần.
- Automation: [ ] augment [X] conditional [ ] automate — lý do theo cost-of-error: Sai lệch deadline hoặc nội dung lớp học gây hậu quả rất đắt (mất điểm, mất niềm tin), nên bot chỉ tự trả lời khi có dữ liệu chắc chắn trong Vector DB; khi mơ hồ hoặc không có dữ liệu, bot từ chối làm liều và chuyển case cho TA.
- §4b. Nguyên tắc đã áp dụng (≥4 — HAX/PAIR, xem guide):
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | G1 — Rõ phạm vi | Bot chào và thông báo rõ ``Trả lời dựa trên kênh thông báo/bài học đã ingest từ Discord`` để user biết phạm vi dữ liệu. |
  | G2 — Rõ giới hạn | Mỗi câu trả lời kèm độ tin cậy và citation source link tới tin nhắn gốc, hiển thị kênh và timestamp rõ ràng. |
  | G10 — Thu hẹp khi nghi ngờ | Nếu truy vấn không đủ dữ liệu hoặc mơ hồ, bot chủ động hỏi lại một câu hoặc trả lời "Em chưa tìm thấy thông tin này trong tài liệu, đã ghi nhận để TA hỗ trợ nhé" thay vì đoán bừa. |
  | G8 — Gạt bỏ dễ dàng | Thiết kế flow cho phép user bỏ qua bot và hỏi TA/đọc link nguồn nếu bot không tìm ra, tránh chặn flow học viên. |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8) [bảng theo guide §2.5]

|Phủ 4 kiểu tình huống	|Số case|

|Không có trong tài liệu|	4|
|Mơ hồ/thiếu ngữ cảnh|	4|
|Không được phép làm	|3|
|Hậu quả thật|	13|
|Mỗi kiểu đạt ≥2?|	CÓ|

`tình huống cụ thể | lớp | hành vi mong muốn (nói gì, hiện gì, cho user làm gì tiếp) | nguyên tắc áp (G../PAIR)`. 


## §6. Bốn đường đi của trải nghiệm
- Happy path: · Low-confidence (②): · Failure/không căn cứ (①): · Correction (user sửa):
- Khi bị đòi ngoài phạm vi (③): · Case đặc thù domain (④):

## §7. Kiểm thử
- Chiều chất lượng + định nghĩa kiểm chứng được:
- Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/):
- Quality bar (chốt từ 23:59, giữ nguyên sau đó): "Đạt khi ≥ ___% qua bộ, và ___"
- Kết quả các lượt chạy (bảng % — cập nhật đến trước CP6):

## §8. Phân công & kế hoạch
- Phân công có tên: spec / evidence / prompt / code / demo
- Willing users (≥3 tên) + kế hoạch vòng validation CP5 (3 câu hỏi, ai log):
- Multi-prototype (nếu làm): trục khác biệt của ≥2 phương án + lý do chọn:

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
```
