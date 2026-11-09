# Chatbot Defense Arena: chọn lọc ý tưởng và phân việc backend / frontend

## 1. Hai bản đang có
- Bản của Đông (kế hoạch trong docs/PLAN.md): Python + Streamlit, Gemini miễn phí qua call_ai, level và Endless viết bằng JSON, judge bằng code, lưu dữ liệu ẩn danh lên Supabase có ô đồng ý, làm theo từng phase bằng Claude Code.
- Bản của James (file handoff): demo chạy được, một file HTML cộng server.py gọi API Claude, 12 level trong 3 thế giới (Café, Dealership, University), 4 vòng bản đồ, thẻ luật có chi phí, Endless nhiều đợt, bảng kỷ lục. Chưa chạy thử AI thật, chưa có ô đồng ý lưu dữ liệu.

## 2. Giữ ý nào của bên nào
Lấy từ demo của James:
- Bản đồ 4 vòng (công khai 10, nội bộ 25, nhạy cảm 50, lõi 150 điểm). Lõi bị lộ thì thua cả vòng.
- Thẻ luật có 4 loại: phòng thủ, nhiễu (decoy), bẫy (trap), thẻ trang trí (không có tác dụng). Game không bao giờ nói thẻ nào là thừa.
- Mỗi lượt chơi tạo một "cửa hàng thẻ" khác nhau để không thể học thuộc một bộ thẻ đi qua mọi lượt.
- Endless là một chuỗi các đợt, khó dần, qua đợt cần ít nhất 1 sao, thua một đợt là kết thúc, điểm đợt có hệ số tăng dần.
- 12 level chia 3 thế giới (làm sau cùng nếu còn thời gian).
- Giao diện chat: khách và kẻ tấn công bên trái, chatbot bên phải, bản đồ đổi sau mỗi tin nhắn, có thanh tua lại.
- Cách kiểm thử: đối chiếu judge với bộ chấm điểm trên hàng nghìn lựa chọn ngẫu nhiên.

Giữ từ kế hoạch của Đông (backend):
- Python + Streamlit, Gemini miễn phí qua call_ai, chế độ AI giả mặc định (chạy được không cần key).
- Nội dung level và Endless nằm trong file JSON.
- Judge bằng code (không để AI chấm).
- Lưu dữ liệu ẩn danh lên Supabase, có ô đồng ý, mặc định không tick.
- Ngưỡng chấm điểm trong MASTER_PROMPT mục 4.3.

Bỏ khỏi phạm vi hackathon: bảng kỷ lục công khai (cần quyền đọc, mâu thuẫn với cách lưu chỉ ghi), vật phẩm hoặc power up, bảng điều khiển nhập key trong game.

## 3. Điểm khác cần chú ý
- Demo dùng API Claude trả phí. Kế hoạch dùng Gemini miễn phí. Giữ Gemini, vì call_ai cho phép đổi nhà cung cấp sau này.
- Demo là HTML. Kế hoạch là Streamlit. Giữ Streamlit để khớp hợp đồng giữa backend và frontend. James dùng demo làm tài liệu tham khảo giao diện.
- Handoff nói luật natHacks yêu cầu mọi code phải viết trong thời gian sự kiện và lịch sử commit được kiểm tra. Vì vậy KHÔNG đưa file HTML của demo vào repo. Viết lại từ đầu. Hãy kiểm tra lại điều khoản trên trang của ban tổ chức để chắc chắn.

## 4. Chia việc
Backend (Đông, ROLE=A): engine/, scenarios/, tests/, storage.
- Phase 0 đến 5, 9, 10, 12A, 13A.
- Nâng cấp sau đó: 14 (Endless nhiều đợt), 16 (cửa hàng thẻ mỗi lượt), 18 (thêm 2 thế giới).

Frontend (James, ROLE=B): app.py, ui/, README.md.
- Phase 6, 7, 8, 11, 12B, 13B.
- Nâng cấp sau đó: 15 (giao diện Endless nhiều đợt), 17 (đường đi level và thế giới).

Hợp đồng chung: mục 4 của MASTER_PROMPT.md. Muốn đổi tên hàm hoặc dạng dữ liệu thì phải ghi vào docs/PROGRESS.md mục Decisions và báo cho người kia.

## 5. Thứ tự ưu tiên (hạn chót thứ Hai 11 giờ sáng giờ Mountain)
1. Phase 0 đến 7: có game chơi được (tutorial_1, bản đồ, chat, kết quả). Làm trước.
2. Phase 8 đến 11 và 13: hướng dẫn, thêm level, Endless, README. Bắt buộc có README trước khi nộp.
3. Phase 12 (Supabase) và 14 đến 18: nâng cấp, chỉ làm khi còn thời gian.

## 6. Việc riêng của frontend (James) đã chốt thêm
- Tốc độ chat khi phát lại: mặc định hiện từng tin một, cách nhau khoảng 2 giây (tin dài thì lâu hơn). Có lựa chọn tốc độ (Chậm, Bình thường, Nhanh), nút Tạm dừng, giữ nút Next message và thanh tua lại. Áp dụng cho cả Level mode và Endless vì hai chế độ dùng chung màn hình phát lại (Phase 7). Backend không phải sửa gì.

## 7. Tên hàm và dữ liệu chung (hợp đồng giữa backend và frontend)
Chuẩn duy nhất là mục 4 của MASTER_PROMPT.md. Ai muốn đổi thì nhắn người kia trước, rồi ghi vào docs/PROGRESS.md mục Decisions.

Hàm James gọi từ engine của Đông:
| File | Hàm | Nhận vào | Trả về |
|---|---|---|---|
| engine/scenarios.py | load_scenario(id) | id như "cafe" | dict scenario đã kiểm tra |
| engine/scenarios.py | list_scenarios() | không | danh sách scenario |
| engine/scenarios.py | get_guide_steps(level) | một level | danh sách bước hướng dẫn, rỗng nếu không có |
| engine/level.py | pick_package(level, rng=None) | level | chỉ số gói tấn công |
| engine/level.py | run_level(level, chosen_rules, package_index) | level, id luật đã chọn, chỉ số gói | dict gồm events, security, helpfulness, core_hacked, rules_used, package_index |
| engine/level.py | explain_result(level, chosen_rules, result) | như trên | danh sách giải thích từng lỗi |
| engine/grading.py | grade_level(result, min_rules) | kết quả, số luật tối thiểu | grade, stars, score, security_pct, helpfulness_pct |
| engine/save.py | export_game(record), import_game(text) | dict hoặc chuỗi JSON | chuỗi JSON hoặc dict |
| engine/endless.py | run_section(section, player_rules, package_index) | section, chữ luật, chỉ số gói | cùng dạng run_level cộng rules_chars |
| engine/storage.py | new_session_id(), record_play(...) | xem mục 4.6 | id mới, hoặc True hoặc False |
| engine/ai.py | call_ai(...) | chỉ engine dùng | chuỗi trả lời |

Thêm khi làm các phase nâng cấp: build_shop, min_rules_for_package (Phase 16), start_run, play_section (Phase 14).

Tên trường dữ liệu phải khớp:
- Mỗi event có step, sender, text, reply, zone, outcome, map.
- sender chỉ nhận "attacker" hoặc "customer".
- outcome chỉ nhận "blocked", "leaked", "served", "refused".
- map có giá trị "safe" hoặc "lost" theo từng zone.
- Mỗi zone có id, label, ring, points. ring chỉ nhận "outer", "inner", "sensitive", "core".
- Mỗi luật có id, label, text, cost.
- grade chỉ nhận "perfect", "stars", "fail", "lose".

Quy ước chung:
- Id level là tutorial_1, tutorial_2, level_1 và tiếp theo.
- Engine không ghi file và không gọi giao diện. Giao diện không gọi call_ai trực tiếp.
- Dữ liệu mẫu để James dựng giao diện sớm nằm ở docs/sample_results.json, đúng dạng với kết quả thật.

Cách giữ không lệch nhau:
1. Chỉ dùng mục 4 làm chuẩn, đổi gì phải báo nhau trước.
2. Mỗi người chỉ sửa thư mục của mình (Đông: engine/, scenarios/, tests/. James: app.py, ui/).
3. James gọi engine qua file adapter ui/data.py.
4. Cả hai chạy git pull thường xuyên và chạy python tests/run_all.py trước khi đẩy code.

## 8. Quy trình Git của nhóm (theo CLAUDE.md đã có trong repo)
- Không ai push thẳng lên main. Mỗi người làm trên nhánh riêng (ví dụ dong/phase-1, james/phase-6), đẩy nhánh lên rồi mở Pull Request. Người còn lại xem qua và bấm Merge.
- Trước mỗi phase mới, chạy git checkout main và git pull để lấy bản mới nhất.
- Repo hiện đã có bản prototype cũ (engine, scenarios, app.py). Kế hoạch mới thay thế nó dần theo từng phase. Phase 0 sẽ sửa CLAUDE.md, thay phần hợp đồng cũ (run_round, resolve_choice) bằng hợp đồng mới ở mục 4 của MASTER_PROMPT.md. Hai bạn cần đồng ý việc này trước khi bắt đầu.
- Bản prototype cũ có chế độ Easy (chọn thẻ trắc nghiệm). Chế độ đó đã bị bỏ trong kế hoạch mới (Level mode chọn luật, Endless tự viết luật).

## 9. Nội dung level đã viết sẵn (không để Claude Code tự bịa)
- docs/cafe.json chứa sẵn nội dung game: 4 level (tutorial_1, tutorial_2, level_1, level_2) và 2 section Endless, đúng định dạng của hợp đồng mục 4. Đã kiểm tra cân bằng bằng docs/check_cafe_design.py (kết quả ERRORS: 0).
- Phase 2 chỉ chép file này sang scenarios/cafe.json và viết bộ nạp (loader). Phase 9 chỉ viết test cân bằng, không viết lại level. Phase 10 dùng sẵn 2 section.
- Muốn sửa lời thoại hay thêm level thì sửa trực tiếp docs/cafe.json (và scenarios/cafe.json), rồi chạy: python docs/check_cafe_design.py docs/cafe.json
