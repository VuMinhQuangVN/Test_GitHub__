# Đánh giá tổng thể & Đề xuất nâng cấp — AI_Video_Factory

*Dựa trên review trực tiếp toàn bộ source code trong repo `Test_GitHub__/AI_Video_Factory` (~7.000 dòng Python, PyQt6 + Playwright).*

---

## 1. Project này thực chất là gì?

Đây là một ứng dụng desktop (PyQt6) đóng vai trò **"đạo diễn"** điều khiển trình duyệt Chrome thật (qua Playwright) để tự động:

- Tạo ảnh sản phẩm/người mẫu bằng **Gemini Flow** và **ChatGPT** (web UI, không phải API chính thức cho phần này)
- Tạo video từ ảnh (Flow "Banana Pro")
- Ghép video, gắn watermark che logo (`engines/video_editor.py`, dùng MoviePy)
- Quản lý nhiều **tài khoản Chrome profile** ("Nick") để xoay vòng khi hết credit
- Quản lý nhiều **API key Gemini** để xoay vòng khi hết quota (`core/key_manager.py`)
- Ẩn dấu vết tự động hoá: xoá cờ `navigator.webdriver`, tắt `--enable-automation`, tiêm JS để vượt qua bot-detection (`core/browser_manager.py`)

**Nhận xét thẳng thắn (quan trọng hơn cả code):** phần lõi của hệ thống là automation trên giao diện web của Google/OpenAI kèm kỹ thuật né bot-detection và xoay vòng nhiều tài khoản để lách giới hạn credit. Đây là vùng rủi ro cao về ToS (rất dễ bị khoá hàng loạt tài khoản) và không ổn định về mặt kỹ thuật (Google/OpenAI đổi UI là selector gãy ngay — thực tế bạn đã có `debug_selector.py`, `debug_chatgpt.py` cho thấy việc này đã xảy ra). Mình sẽ đánh giá code trên tinh thần kỹ thuật, nhưng khuyến nghị lớn nhất ở cuối báo cáo là **cân nhắc chuyển phần tạo ảnh sang API chính thức** (Gemini đã có API, phần ChatGPT/Flow thì không) để giảm rủi ro và tăng độ ổn định — đây cũng là hướng "nâng cấp" bền nhất về lâu dài.

---

## 2. Đánh giá riêng thư mục `engines/` (đúng như bạn nghi ngờ)

| File | Tình trạng | Kết luận |
|---|---|---|
| `engines/video_editor.py` | Đang được dùng (import trong `ui/pages/video_merger_page.py`) | **Giữ lại**, đây là phần ghép video/watermark thật sự chạy |
| `engines/flow/image_engine.py` | **Không có bất kỳ file nào trong project import class `ImageEngine`** | **Code chết (dead code)** |
| `engines/flow/video_engine.py` | Toàn bộ file bị comment, class `VideoEngine` không được import ở đâu | **Code chết 100%, an toàn xoá** |

Mình đã grep toàn repo để xác nhận: logic tạo ảnh/video thật sự đang chạy nằm ở `ui/workers/image_worker.py` và `ui/workers/video_worker.py` — đây rõ ràng là **bản viết lại sau này** của `engines/flow/*`, nhưng thư mục cũ không được dọn. Đây chính xác là "thư mục thừa" bạn cảm nhận được — trực giác của bạn đúng.

**Các "rác" tương tự khác mình phát hiện được** (không chỉ riêng `engines/`):

- `pages/` (Page Object cho bot – Selenium/Playwright) và `ui/pages/` (màn hình PyQt) **trùng tên thư mục nhưng là hai thứ khác nhau** → gây nhầm lẫn cực lớn khi đọc code, kể cả với người quen thuộc project. Nên đổi tên, ví dụ `pages/` → `bots/` hoặc `web_pages/`.
- `ui/workers/video_worker.py`: **68/189 dòng đầu file là code cũ bị comment**, class `VideoWorker` thật nằm phía dưới → nên xoá phần comment, dùng git history nếu cần xem lại.
- `core/browser_manager.py`: y hệt tình trạng trên — nửa đầu file là bản cũ bị comment, bản mới nằm dưới.
- `AI_Video_Factory/logs/`: **21 file `.zip` trace debug (Playwright trace)** đang nằm trong git — đây là file rác runtime, không nên commit.
- `REDME.doc` (gõ nhầm README), `chatgpt_account_status` (file không đuôi, không rõ định dạng) — rác đặt nhầm chỗ.
- Có `__pycache__/*.pyc` được commit thẳng vào git ở nhiều thư mục — không nên commit.
- Không có `.gitignore`, không có `requirements.txt` — ai clone về cũng không biết cài gì, và dễ commit nhầm rác/`.pyc`/log lần nữa.

---

## 3. Các vấn đề kỹ thuật đáng chú ý trong code đang chạy

1. **Đường dẫn hard-code Windows-only** (`main.py`): `base_storage = "F:/Data_Tool" if os.path.exists("F:/") else ...` và `chrome_exe = r"C:\Program Files\Google\Chrome\..."` trong `browser_manager.py`. App hiện chỉ chạy được trên máy có ổ `F:` và Chrome cài ở đường dẫn mặc định Windows — không portable, không chạy được trên máy khác/macOS/Linux nếu không sửa tay.
2. **`core/api_gemini.py`** dùng model `gemini-1.5-flash` — đây là bản cũ, nên nâng lên dòng model Gemini hiện hành (2.x) để cải thiện chất lượng/tốc độ và tránh bị deprecate.
3. **Except chung chung nuốt lỗi** (`except: return text`, `except: pass` xuất hiện nhiều nơi) — khi bot gãy vì Google đổi UI, lỗi bị nuốt im lặng, rất khó debug production. Nên log rõ loại lỗi thay vì bare `except`.
4. **`database/*.json` làm "database"**: không có khoá đồng thời (concurrency lock), nếu nhiều worker (QThread) ghi cùng lúc vào `api_keys.json`/`account_status.json` có nguy cơ race condition/ghi đè mất dữ liệu. Vì đang chạy đa luồng (nhiều Chrome profile song song), rủi ro này thực tế chứ không lý thuyết.
5. **Không có test tự động thật sự** — các file `test_*.py` ở root (`test_video_flow.py`, `test_chatgpt_gui.py`, `test_ausynclab.py`) là script chạy tay để debug bot, không phải unit test (không dùng `pytest`/`unittest`, không assert). Không có CI nào chạy chúng.
6. **UI và logic nghiệp vụ dính chặt vào nhau**: `ui/workers/*_worker.py` vừa chứa logic điều khiển trình duyệt, vừa emit signal cho UI, vừa xử lý business rule (đổi nick khi hết credit, sửa prompt khi render fail...). Rất khó viết test, khó tái sử dụng logic này ở nơi khác (ví dụ chạy headless/CLI/server).
7. **Bảo mật key**: `database/api_keys.json` hiện đang trống (may mắn) nhưng đây là **file chứa API key nằm trong thư mục sẽ bị git track** nếu không có `.gitignore` — chỉ cần một lần bạn add key vào rồi `git add .` là leak key lên GitHub công khai. Đây là rủi ro nghiêm trọng nhất repo đang có, cần xử lý **trước khi làm gì khác**.

---

## 4. Đề xuất roadmap nâng cấp (ưu tiên theo mức độ khẩn cấp)

### Giai đoạn 0 — Việc phải làm ngay (rủi ro bảo mật, 30–60 phút)
- [ ] Thêm `.gitignore` chặn: `__pycache__/`, `*.pyc`, `database/api_keys.json`, `database/*_account_status.json`, `logs/*.zip`, `profiles/`
- [ ] Tạo `database/api_keys.example.json` mẫu (rỗng) để người khác biết cấu trúc, còn file thật không commit
- [ ] Xoá toàn bộ `.pyc`/`__pycache__` đang bị track khỏi git
- [ ] Xoá 21 file trace `.zip` trong `logs/` khỏi git (giữ lại local nếu cần debug)
- [ ] Xoá `REDME.doc`, đổi tên/xử lý file `chatgpt_account_status`
- [ ] **Nếu trước đây từng commit key thật vào bất kỳ commit nào (kể cả đã xoá sau đó) → key đó coi như đã lộ, cần revoke/tạo key mới ngay**, vì lịch sử git vẫn còn trong `.git/objects`

### Giai đoạn 1 — Dọn dẹp & chuẩn hoá (1–2 buổi)
- [ ] Xoá `engines/flow/image_engine.py` và `engines/flow/video_engine.py` (dead code đã xác nhận)
- [ ] Xoá toàn bộ block code cũ bị comment trong `browser_manager.py`, `video_worker.py`
- [ ] Đổi tên `pages/` → `bots/` (hoặc tương tự) để hết nhầm lẫn với `ui/pages/`
- [ ] Viết `requirements.txt` (PyQt6, playwright, moviepy, google-generativeai, pillow...) + hướng dẫn cài `playwright install chromium`
- [ ] Viết lại `README.md` thật (mục đích app, cách cài, cách chạy, cấu trúc thư mục)
- [ ] Sửa đường dẫn hard-code (`F:/Data_Tool`, `C:\Program Files\...`) → đọc từ file config/`.env`, có fallback hợp lý cho mọi OS

### Giai đoạn 2 — Refactor cấu trúc (tách logic khỏi UI)
- [ ] Đưa business logic ra khỏi `ui/workers/*.py` vào các class ở `core/` hoặc `services/` (worker chỉ nên là lớp mỏng gọi service rồi emit signal)
- [ ] Chuẩn hoá xử lý lỗi: định nghĩa exception riêng (`BotDetectionError`, `OutOfCreditError`...) thay vì so sánh chuỗi `"OUT_OF_CREDIT"`, `"STUCK_AT_99"` rải rác khắp nơi
- [ ] Thêm logging bằng module `logging` chuẩn (có level, ghi file) thay vì `print()`
- [ ] Thêm lock (threading.Lock) khi nhiều worker cùng ghi `database/*.json`, hoặc chuyển sang SQLite nếu dữ liệu lớn dần

### Giai đoạn 3 — Nâng cấp tính năng/độ bền
- [ ] Nâng model Gemini lên bản hiện hành thay vì `gemini-1.5-flash`
- [ ] Cân nhắc nghiêm túc: phần nào đang phải "giả lập người dùng" trên web UI (đặc biệt ChatGPT) có API chính thức thay thế được không — giảm phụ thuộc vào selector DOM dễ vỡ và giảm rủi ro tài khoản bị khoá
- [ ] Viết vài unit test thật cho phần logic thuần (không cần trình duyệt): `prompt_builder.py`, `key_manager.py`, `config_manager.py`, `video_editor.time_to_seconds`
- [ ] Thêm cơ chế retry/backoff có giới hạn rõ ràng thay vì loop `while` không có giới hạn số lần thử

---

## 5. Tóm tắt ưu tiên nếu bạn chỉ làm được 3 việc tuần này

1. **`.gitignore` + gỡ `api_keys.json`/`.pyc`/log rác khỏi git** — rủi ro bảo mật, làm trước tiên.
2. **Xoá `engines/flow/*` (dead code) + dọn code comment cũ** — đúng phần bạn hỏi, dọn sạch để đọc code không bị rối nữa.
3. **Viết `requirements.txt` + README thật + sửa đường dẫn hard-code** — để bất kỳ ai (kể cả bạn sau này mở lại project) cũng chạy được mà không phải đoán.

Nếu bạn muốn, mình có thể bắt tay làm luôn Giai đoạn 0 + xoá dead code trong `engines/` ngay bây giờ — chỉ cần bạn xác nhận là được, mình sẽ chỉnh trực tiếp và show diff cho bạn xem trước khi bạn push lên GitHub thật.
