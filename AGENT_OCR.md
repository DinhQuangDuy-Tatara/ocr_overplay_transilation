# AGENT_OCR — Real-Time Screen Translator (RTST)

> Tài liệu hợp nhất từ `testdoc.md` (đặc tả gốc) và `nhung van de.md` (review kỹ thuật). Các điều chỉnh trong review được ưu tiên khi có khác biệt; nội dung gốc còn phù hợp được giữ lại.

# TECHNICAL SPECIFICATION & DEVELOPMENT PLAN

**Dự án:** Real-Time Screen Translator (RTST)

## A. Product Overview

- **Mô tả sản phẩm:** RTST là một phần mềm desktop hoạt động dưới dạng Overlay, cho phép dịch nội dung văn bản (đặc biệt là truyện tranh, manhwa) trực tiếp trên màn hình theo thời gian thực mà không làm gián đoạn trải nghiệm người dùng.
    
- **Mục tiêu và giá trị cốt lõi:** Loại bỏ rào cản ngôn ngữ một cách liền mạch (seamless). Giảm thiểu thao tác thủ công (chụp ảnh, copy/paste). Cung cấp trải nghiệm "đọc bản gốc như đọc bản dịch".
    
- **Đối tượng sử dụng:** Người đọc truyện tranh nước ngoài (Hàn, Nhật, Trung, Anh), người học ngoại ngữ, game thủ.
    
- **Tình huống sử dụng thực tế (Use Case):** Người dùng đang cuộn trang đọc Manhwa tiếng Hàn trên trình duyệt. Họ bật RTST, quét chọn khu vực hiển thị truyện. Khi họ cuộn trang, RTST tự động nhận diện chữ tiếng Hàn trong bong bóng thoại, xóa chữ gốc, chèn chữ tiếng Việt lên trên với độ trễ thấp nhất có thể.
    
- **Phạm vi sản phẩm (Scope):**
    
    - _In-scope:_ Dịch truyện tranh, văn bản tĩnh trên màn hình. Hỗ trợ Linux/Wayland ưu tiên, kiến trúc mở cho Windows.
        
    - _Out-of-scope:_ Dịch video/phim (đòi hỏi xử lý audio/subtitle phức tạp), dịch toàn bộ màn hình hệ điều hành (chỉ tập trung vùng được chọn để tối ưu hiệu năng).
        

## B. Functional Requirements

|**Chức năng**|**Phân loại**|**Mô tả**|**Input -> Process -> Output**|**Phụ thuộc**|
|---|---|---|---|---|
|**1. Region Selection**|Must-have|Cho phép người dùng vẽ một bounding box để xác định vùng cần theo dõi.|Input: Tọa độ chuột (x, y, w, h). Process: Lưu tọa độ. Output: Tọa độ vùng theo dõi.|Wayland Screen Capture|
|**2. Screen Capture**|Must-have|Chụp ảnh vùng đã chọn theo tần số quét nhất định.|Input: Tọa độ vùng. Process: Giao tiếp với OS để lấy pixel data. Output: Image buffer (RGB).|Region Selection|
|**3. Auto Detection**|Should-have|So sánh frame hiện tại với frame trước đó để xem có thay đổi không.|Input: Image buffer 1 & 2. Process: Tính toán SSIM hoặc Pixel Diff. Output: Boolean (True/False).|Screen Capture|
|**4. OCR**|Must-have|Trích xuất văn bản và tọa độ từ ảnh.|Input: Image buffer. Process: Chạy mô hình OCR. Output: Text, Bounding Boxes, Confidence score.|Screen Capture|
|**5. Translation**|Must-have|Dịch text từ ngôn ngữ gốc sang ngôn ngữ đích.|Input: Text gốc. Process: Gọi Local Model hoặc API. Output: Text đích.|OCR|
|**6. Cache**|Must-have|Lưu kết quả dịch để dùng lại.|Input: Text gốc/Hash ảnh. Process: Tra cứu Database. Output: Cache Hit/Miss.|OCR, Translation|
|**7. Text Replacement**|Should-have|Xóa/Làm mờ text gốc, chèn text dịch sao cho tự nhiên.|Input: Bounding Box, Image, Text đích. Process: Inpainting (OpenCV) -> Render Text. Output: Rendered Image.|OCR, Translation|
|**8. Overlay Rendering**|Must-have|Hiển thị kết quả lên một cửa sổ trong suốt đè lên ứng dụng gốc.|Input: Rendered Image. Process: Cập nhật GUI. Output: Overlay Window trên màn hình.|Tất cả|
|**9. User Controls**|Must-have|Bảng điều khiển (Start/Stop, Settings, v.v.).|Input: Thao tác UI. Process: Gửi signal đến Core. Output: Thay đổi trạng thái app.|Độc lập|

## C. Technical Research

### 1. Screen Capture (Khó nhất trên Wayland)

- **Wayland hạn chế nghiêm ngặt việc ứng dụng tự ý đọc màn hình (security model).** X11 APIs sẽ không hoạt động.
    
- _Giải pháp 1: `grim` + `slurp`._ Dùng CLI tool để chụp màn hình. Dễ làm nhưng chậm, tạo overhead lớn do phải ghi/đọc file hoặc pipe liên tục.
    
- _Giải pháp 2: XDG Desktop Portal (PipeWire/ScreenCast)._ Tiêu chuẩn của Wayland.
    
- **Đề xuất:** Dùng thư viện Python wrap lại Pipewire hoặc dùng DBus API để giao tiếp với `xdg-desktop-portal-wlr`. Đối với MVP, có thể dùng tạm `grim` qua subprocess để proof-of-concept, nhưng Production phải dùng **PipeWire**.
    

### 2. OCR (Optical Character Recognition)

- _Tesseract:_ Nổi tiếng, nhưng nhận diện tiếng Hàn (đặc biệt chữ dọc) khá tệ.
    
- _EasyOCR:_ Chạy local, hỗ trợ nhiều ngôn ngữ, GPU/CPU, tốt cho tiếng Hàn.
    
- _PaddleOCR:_ Rất nhanh, nhẹ, độ chính xác cực cao cho CJK (Trung, Nhật, Hàn).
    
- _MangaOCR:_ Cực tốt cho manga Nhật, nhưng không hỗ trợ Hàn.
    
- **Đề xuất:** **PaddleOCR**. Cân bằng tuyệt vời giữa tốc độ và độ chính xác cho tiếng Hàn/Trung/Nhật/Anh. Có thể chạy local (ONNX runtime).
    

### 3. Machine Translation

- _Local (NLLB-200, CTranslate2, MarianMT):_ Riêng tư, không tốn phí mạng, nhưng tốn RAM/VRAM và có thể chậm.
    
- _Cloud API (DeepL, Google Cloud, Sugoi):_ Nhanh, chính xác, nhưng tốn phí hoặc bị rate-limit.
    
- **Đề xuất:** Thiết kế theo kiến trúc Interface. MVP sử dụng **Google Translate API** (phiên bản free/scraping qua thư viện `deep-translator`) để đảm bảo tiến độ. Sau đó tích hợp **CTranslate2 (NLLB)** để người dùng chọn chạy local.
    

### 4. Text Replacement (Xóa chữ gốc)

- **Đề xuất:** Sử dụng **OpenCV**. Tạo mask từ Bounding Box của OCR, dùng thuật toán Inpainting (Telea hoặc Navier-Stokes) để lấp đầy nền. Sau đó render text mới lên trên. Tốc độ rất nhanh, chi phí tính toán thấp.
    

### 5. Overlay Rendering & GUI Framework

- Wayland không cho phép các cửa sổ "always on top, click-through, global" một cách dễ dàng như X11.
    
- Niri (tiling WM) quản lý cửa sổ theo dạng cột. Cần cấu hình rule để cửa sổ này là floating.
    
- **Đề xuất:** Dùng **PySide6 (Qt6 cho Python)**. Qt6 có hỗ trợ Wayland native. Sử dụng Window flag `FramelessWindowHint` và cấu hình background transparent.
    
- _Lưu ý Wayland:_ Để click-through (chuột xuyên qua overlay), có thể phải dùng protocol `wlr-layer-shell` (qua thư viện `gtk4-layer-shell` nếu dùng GTK) hoặc cấu hình window rule cụ thể của Niri. Cần test kỹ phần này.
    

### 6. Ngôn ngữ lập trình

- **Đề xuất:** **Python 3.11+**.
    
- _Lý do:_ Hệ sinh thái CV (OpenCV), ML (PaddleOCR, HuggingFace) quá mạnh. Tốc độ phát triển nhanh. Hiệu năng có thể bù đắp bằng việc các thư viện lõi (OpenCV, OCR) đều viết bằng C++. Nếu sau này cần tối ưu, sẽ chuyển core sang C++ hoặc Rust, Python chỉ làm UI.
    

## D. System Architecture

### 1. Đề xuất Kiến trúc tổng thể

Hệ thống sử dụng kiến trúc **Producer - Consumer** kết hợp **Event-Driven**, chạy trên các Thread/Process độc lập để không làm block UI.

Đoạn mã

```
graph TD
    subgraph UI_Layer [User Interface Layer]
        ControlPanel[Control Panel]
        Overlay[Transparent Overlay Window]
        RegionSelector[Region Selector]
    end

    subgraph Core_Engine [Core Processing Engine]
        CaptureThread[Capture Thread / PipeWire]
        ChangeDetect[Change Detector SSIM]
        Vision[Vision Module OCR + Masking]
        Translator[Translation Module]
        Renderer[Text Rendering Module]
        Cache[(SQLite / In-Memory Cache)]
    end

    ControlPanel -->|Config & Commands| Core_Engine
    RegionSelector -->|Bounding Box| CaptureThread
    CaptureThread -->|Raw Frame| ChangeDetect
    ChangeDetect -->|Changed Frame| Vision
    Vision -->|OCR Text & Boxes| Translator
    Vision <-->|Get/Set Mask| Cache
    Translator <-->|Check/Save Translation| Cache
    Translator -->|Translated Text| Renderer
    Vision -->|Background Inpainted Image| Renderer
    Renderer -->|Final Image Overlay| Overlay
```

### 2. Luồng dữ liệu (Pipeline)

1. Capture Thread lấy frame từ Wayland (ví dụ 5 FPS).
    
2. Change Detector so sánh frame hiện tại với frame T-1. Nếu giống nhau > 98%, bỏ qua để tiết kiệm CPU.
    
3. Nếu khác, gửi frame tới Vision Module. Vision chạy PaddleOCR để lấy Text + Bounding Box.
    
4. Gửi Text qua Cache. Nếu có kết quả -> Lấy ra. Nếu không -> Gọi Translation API -> Lưu Cache.
    
5. Xóa text gốc bằng OpenCV Inpaint dựa trên Bounding Box.
    
6. Render text tiếng Việt vào đúng vị trí Bounding Box (có tự động scale font chữ cho vừa khung).
    
7. Xuất ảnh đã xử lý lên Transparent Overlay Window.
    

## E. User Interface & User Experience

- **Main Window (Control Panel):** Giao diện nhỏ gọn. Có nút [Start Translation], [Select Region], [Settings].
    
- **Region Selection:** Khi bấm, màn hình tối lại, con trỏ chuột đổi thành dấu thập. Người dùng kéo thả để vẽ một hình chữ nhật.
    
- **Translation Overlay:** Một cửa sổ hoàn toàn trong suốt, không viền, nằm đè đúng lên vị trí hình chữ nhật đã chọn. Nó chỉ hiển thị ảnh đã được xóa nền chữ gốc và đè chữ tiếng Việt lên. Người dùng bấm chuột xuyên qua nó để lật trang trên trình duyệt bên dưới.
    
- **Settings:** Chọn ngôn ngữ đích/nguồn, chọn OCR Engine, chọn Translation Engine (Local/API), độ trễ (FPS capture).
    

## F. Development Roadmap

### Phase 1: Research & Proof of Concept (PoC)

- **Mục tiêu:** Giải quyết các rủi ro kỹ thuật lớn nhất trên Wayland/Niri.
    
- **Công việc:**
    
    - Viết script Python capture màn hình bằng DBus/Pipewire hoặc `grim`.
        
    - Viết script tạo cửa sổ trong suốt bằng PySide6 và cho phép click-through trên Niri.
        
- **Đầu ra:** Hai script độc lập chạy thành công.
    
- **Acceptance Criteria:** Chụp được ảnh màn hình không cần quyền sudo. Cửa sổ trong suốt hiện lên, chuột click được vào app bên dưới.
    

### Phase 2: Core Pipeline (No UI)

- **Mục tiêu:** Xây dựng backend xử lý ảnh và ngôn ngữ.
    
- **Công việc:**
    
    - Tích hợp PaddleOCR.
        
    - Tích hợp deep-translator (Google API).
        
    - Viết thuật toán OpenCV Inpainting và Text Rendering (Pillow).
        
- **Đầu ra:** Một script CLI nhận vào ảnh tiếng Hàn, xuất ra ảnh đã thay chữ tiếng Việt.
    
- **Acceptance Criteria:** Text nhận diện đúng > 90%, text mới nằm gọn trong bong bóng thoại.
    

### Phase 3: The MVP (Minimum Viable Product)

- **Mục tiêu:** Ghép nối UI và Core Pipeline.
    
- **Công việc:**
    
    - Xây dựng Control Panel.
        
    - Tích hợp Region Selection.
        
    - Gắn luồng xử lý: Hotkey -> Capture vùng chọn -> Xử lý (Phase 2) -> Đẩy lên Overlay.
        
- **Đầu ra:** Ứng dụng hoàn chỉnh, người dùng bấm phím tắt, vùng chữ tự động biến thành tiếng Việt (chưa auto-detect).
    
- **Acceptance Criteria:** Toàn bộ luồng từ lúc chọn vùng đến lúc hiện chữ < 2 giây.
    

### Phase 4: Automation & Optimization

- **Mục tiêu:** Tự động hóa và giảm độ trễ (Real-time).
    
- **Công việc:**
    
    - Thêm Capture Thread chạy ngầm (ví dụ 2-5 FPS).
        
    - Viết module Change Detection (SSIM).
        
    - Tích hợp SQLite Caching.
        
- **Acceptance Criteria:** Khi người dùng cuộn trang, chữ tự dịch mà không cần bấm nút. CPU usage < 15% khi không có thay đổi khung hình.
    

### Phase 5: Polish & Windows Port

- **Mục tiêu:** Đóng gói, sửa lỗi và tương thích Windows.
    
- **Công việc:** Trừu tượng hóa module Screen Capture (dùng `mss` hoặc `dxcam` cho Windows, giữ Pipewire cho Linux).
    

## G. Testing Strategy

- **Unit Testing:** Sử dụng `pytest`. Test độc lập các hàm: OCR text extraction, Translation output, SSIM diff logic.
    
- **OCR Accuracy Testing:** Chuẩn bị 100 ảnh Manhwa. Chạy test script so sánh text OCR được với text mẫu (Ground Truth). Mục tiêu > 95% độ chính xác ký tự.
    
- **Performance Testing:** Đo thời gian xử lý pipeline.
    
    - _Chỉ tiêu:_ Capture < 50ms, OCR < 300ms, Translate < 500ms, Render < 50ms. Tổng latency < 1 giây/frame thay đổi.
        
- **Integration Testing:** Test luồng giao tiếp giữa UI Thread và Processing Thread (đảm bảo không bị deadlock/freeze UI).
    

## H. Risks & Technical Challenges

|**Thách thức**|**Phân tích**|**Giải pháp đề xuất**|
|---|---|---|
|**Giới hạn Wayland/Niri (Capture)**|Ứng dụng không thể gọi X11 `XGetImage`. Niri rất khắt khe.|Bắt buộc sử dụng XDG-Desktop-Portal ScreenCast (PipeWire).|
|**Global Overlay & Click-through**|Wayland thường chặn click-through (chuột xuyên thấu) vì bảo mật.|Sử dụng Niri window rules: `default-column-width {}`, thêm thuộc tính `wlr-layer-shell` nếu cần, hoặc yêu cầu người dùng map phím tắt để tạm ẩn Overlay khi cần tương tác.|
|**Nhận diện chữ bong bóng thoại (Nền phức tạp)**|Chữ nằm trên nền vẽ tay, OCR dễ bắt nhầm nét vẽ thành chữ.|Chuyển ảnh sang Grayscale -> Binarization (Otsu threshold) trước khi đưa vào OCR.|
|**Tránh dịch lặp lại / Giảm API Cost**|Chạy 5 FPS x 1 giờ = 18,000 requests, tốn tiền và bị block API.|Hashing OCR Text. Nếu Text = "안녕", tra Cache. Đồng thời dùng Auto Detection (Change Detection), màn hình không đổi thì không OCR.|
|**Che khuất nội dung gốc**|Text tiếng Việt dài hơn tiếng Hàn, bị tràn ra ngoài bong bóng thoại.|Auto-scaling font size: Tính toán diện tích Bounding box, giảm font size nếu text quá dài. Bật Word-wrap.|

## I. MVP Definition

Phiên bản MVP (Phase 3) được định nghĩa chặt chẽ để đảm bảo khả thi:

- **Đầu vào:** Bấm phím tắt hoặc nút để bắt đầu. Người dùng tự chọn vùng tĩnh.
    
- **Xử lý:** Dùng lệnh hệ thống (`grim`) chụp vùng chọn. Chạy PaddleOCR (local) -> Google Translate API (mạng).
    
- **Đầu ra:** Xóa text, in text mới, hiện lên Window trong suốt đè đúng tọa độ đó.
    
- **Loại bỏ khỏi MVP:** Auto-detect khi cuộn trang, Chạy Local AI Translation, Cấu hình GUI phức tạp. (Những thứ này đưa vào Phase 4).
    

## J. Final Deliverables

1. **Danh sách công nghệ đề xuất cuối cùng:**
    
    - Ngôn ngữ: Python 3.11
        
    - UI / Overlay: PySide6 (Qt6)
        
    - Screen Capture: DBus + PipeWire / `grim` + `slurp`
        
    - Image Processing: OpenCV, Pillow
        
    - OCR: PaddleOCR
        
    - Machine Translation: `deep-translator` (Google API) -> CTranslate2 (Tương lai)
        
    - Database/Cache: SQLite3
        
2. **Sơ đồ kiến trúc & luồng xử lý:** Đã cung cấp tại Section D.
    
3. **Danh sách Module Cốt lõi:**
    
    - `capture_engine`: Xử lý giao tiếp OS để lấy ảnh.
        
    - `vision_engine`: Detect thay đổi, Binarization, Inpaint.
        
    - `ocr_engine`: Trích xuất Bounding Box + Text.
        
    - `translation_engine`: Gọi API + Cache.
        
    - `overlay_ui`: Render cửa sổ trong suốt.
        
4. **Task Phát triển MVP (Sprint 1 & 2):**
    
    - [x] Task 1.1: Setup môi trường CachyOS/Niri, cài đặt thư viện.
        
    - [ ] Task 1.2: Viết script `grim` capture vùng chọn trả về numpy array.
        
    - [ ] Task 1.3: Cài đặt và config PaddleOCR cho Korean, viết hàm wrap nhận numpy array trả ra List[Dict(Box, Text)].
        
    - [ ] Task 1.4: Viết hàm gọi Translation API và lưu SQLite.
        
    - [ ] Task 1.5: Viết hàm OpenCV tạo mask từ Box và Inpaint ảnh.
        
    - [ ] Task 1.6: Viết hàm Pillow in chữ tiếng Việt lên tọa độ Box.
        
    - [ ] Task 2.1: Tạo Window PySide6 trong suốt, remove borders.
        
    - [ ] Task 2.2: Ghép nối UI gọi các hàm từ Task 1.x.
        
5. **Tiêu chí dự án hoàn thành:**
    
    - App khởi chạy thành công trên Niri/Wayland.
        
    - Người dùng quét vùng truyện tranh tiếng Hàn, văn bản được thay bằng tiếng Việt hiển thị trên Overlay.
        
    - Chuột lướt, cuộn và click xuyên qua Overlay xuống trình duyệt bên dưới mượt mà.
        
    - Codebase có hướng dẫn setup (README.md) đầy đủ cấu hình Niri.

---

# Technical Review & Required Revisions

Điểm mạnh:

- Đã phân chia các module tương đối rõ ràng.
    
- Đã nhận diện được những khó khăn đặc thù của Wayland.
    
- Có tư duy tách OCR, Translation, Cache và Rendering.
    
- Có roadmap theo từng Phase.
    
- Đã giới hạn MVP thay vì cố làm toàn bộ tính năng ngay từ đầu.
    

## 2. Những vấn đề cần sửa trước khi code

### 2.1. Vấn đề nghiêm trọng nhất: Screen Capture trên Wayland

Ưu tiên xử lý P0

Trong document, bạn đề xuất hai giải pháp:

- MVP: `grim` + `slurp`.
    
- Production: DBus + PipeWire.
    

Hướng này hợp lý, nhưng cần điều chỉnh cách triển khai.

Vấn đề 1: `grim` không phù hợp cho capture liên tục.

`grim` phù hợp để chụp ảnh tĩnh, lấy một frame tại một thời điểm. Nếu gọi subprocess liên tục 2–5 FPS, bạn sẽ phải xử lý overhead của việc tạo tiến trình và truyền dữ liệu ảnh.

Vấn đề 2: PipeWire không tự động cung cấp quyền capture.

Quy trình ScreenCast Portal thực tế gồm:

1. Tạo session.
    
2. Chọn nguồn cần capture.
    
3. Gọi Start.
    
4. Người dùng có thể phải xác nhận quyền chia sẻ màn hình.
    
5. Nhận PipeWire stream và đọc các frame.
    

Đây là một luồng làm việc dài hạn, không đơn giản chỉ gọi một hàm chụp ảnh.

XDG Desktop Portal+1

Tôi đề xuất sửa document như sau:

|Giai đoạn|Công nghệ|
|---|---|
|PoC|grim + slurp|
|MVP|XDG Desktop Portal + PipeWire|
|Production|PipeWire stream liên tục|

Lưu ý: Không nên mặc định `xdg-desktop-portal-wlr` là backend chắc chắn phù hợp với Niri. Cần kiểm tra portal backend đang hoạt động trên hệ thống thực tế.

### 2.2. Overlay và Click-through: Rủi ro lớn nhất của MVP

Ưu tiên xử lý P0

Document đang đề xuất:

- PySide6.
    
- `FramelessWindowHint`.
    
- Transparent background.
    
- Niri window rules.
    
- Click-through.
    

Vấn đề là những thuộc tính này không đồng nghĩa với việc bạn có thể tạo một cửa sổ Overlay toàn màn hình, luôn nằm trên ứng dụng khác và tự động xuyên chuột.

Cần phân biệt ba khả năng:

|Khả năng|Ý nghĩa|
|---|---|
|Transparent|Nhìn xuyên qua vùng không có nội dung|
|Always on top|Luôn nằm phía trên cửa sổ khác|
|Click-through|Sự kiện chuột đi xuyên qua Overlay|

Đây là ba vấn đề khác nhau.

Đặc biệt, Niri window rules có hỗ trợ cấu hình cửa sổ floating, nhưng không thể xem đó là giải pháp hoàn chỉnh cho click-through hoặc global overlay.

GitHub+1

Tôi đề xuất một PoC độc lập:

- Tạo cửa sổ PySide6 không viền.
    
- Background trong suốt.
    
- Hiển thị một đoạn text bất kỳ.
    
- Thử đưa cửa sổ lên trên Firefox.
    
- Thử click và scroll xuyên qua cửa sổ.
    
- Kiểm tra cửa sổ có bị Niri quản lý như một cửa sổ bình thường hay không.
    

Nếu không làm được bước này, toàn bộ kiến trúc Overlay cần được xem xét lại.

### 2.3. OCR: PaddleOCR là lựa chọn hợp lý nhưng chưa đủ đặc tả

Cần cải thiện

Document chọn PaddleOCR là chính. Tôi đồng ý với lựa chọn này để bắt đầu.

Tài liệu PaddleOCR có model nhận diện Korean và English, đồng thời trả về văn bản, bounding box và confidence score.

GitHub+1

Tuy nhiên, cần phân biệt hai công đoạn:

1. Text Detection: Phát hiện vị trí vùng có chữ.
    
2. Text Recognition: Đọc nội dung chữ trong vùng đó.
    

Đối với manhwa, còn một số tình huống khó:

- Chữ Hàn nằm trên nền có nhiều nét vẽ.
    
- Chữ nghiêng hoặc xoay.
    
- Chữ hiệu ứng âm thanh.
    
- Chữ viết tay.
    
- Nhiều dòng chữ trong một bong bóng thoại.
    
- Văn bản dọc.
    

Đề xuất bổ sung vào document:

Không chỉ trả về `Text + Bounding Box`, mà nên có cấu trúc:

```
{    "text": "안녕하세요",    "bbox": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],    "confidence": 0.95,    "language": "ko",    "region_id": 1}
```

Nên giữ bounding box dạng polygon thay vì chỉ dùng hình chữ nhật, vì điều này giúp xử lý vùng chữ nghiêng và tạo mask chính xác hơn.

Ngoài ra, không nên mặc định mọi bounding box đều là một câu thoại độc lập. Cần có bước nhóm các dòng chữ thuộc cùng một bong bóng thoại.

### 2.4. Text Replacement: Inpainting chưa chắc tạo được kết quả đẹp

Cần cải thiện

Trong document, bạn đề xuất OpenCV Inpainting với Telea hoặc Navier-Stokes.

Đây là một phương án tốt để thử nghiệm, nhưng có hạn chế:

Ví dụ, chữ nằm trên nền trắng trong bong bóng thoại thì việc xóa khá dễ.

Nhưng nếu chữ nằm trên nền:

- Tóc nhân vật.
    
- Quần áo.
    
- Phong cảnh.
    
- Hiệu ứng chuyển động.
    
- Họa tiết phức tạp.
    

Thì Inpainting có thể tạo ra những vùng ảnh bị nhòe hoặc biến dạng.

Tôi đề xuất chia Text Replacement thành ba cấp độ:

|Cấp độ|Phương pháp|Độ khó|
|---|---|---|
|Level 1|Che chữ bằng màu nền đơn giản|Thấp|
|Level 2|OpenCV Inpainting|Trung bình|
|Level 3|AI-based Text Removal|Cao|

MVP chỉ nên triển khai Level 1 và Level 2.

Quan trọng hơn, hãy thiết kế để có thể tắt tính năng xóa chữ gốc. Người dùng vẫn có thể xem bản dịch trong một khung nổi nhỏ nếu việc inpainting không đạt chất lượng.

### 2.5. Translation: Cần sửa cách mô tả Google Translate API

Trong document có dòng:

> MVP sử dụng Google Translate API (phiên bản free/scraping qua thư viện deep-translator).

Cách mô tả này chưa chính xác.

`deep-translator` là thư viện cung cấp giao diện cho nhiều dịch vụ dịch thuật. Sử dụng GoogleTranslator thông qua thư viện này không đồng nghĩa với việc đang sử dụng Google Cloud Translation API chính thức.

Bạn nên tách thành:

- Google Cloud Translation API: dịch vụ chính thức, có điều kiện sử dụng và tính phí riêng.
    
- GoogleTranslator qua deep-translator: phương án không chính thức, có thể thay đổi hoặc bị giới hạn.
    
- Local Translation: NLLB/CTranslate2 hoặc mô hình phù hợp khác.
    

Đề xuất kiến trúc:

Tạo một interface chung:

```
class TranslationProvider:    def translate(self, text: str, source: str, target: str):        raise NotImplementedError
```

Sau đó triển khai từng provider độc lập.

Điều này giúp đổi dịch vụ mà không cần sửa OCR, UI hay Overlay.

### 2.6. Cache và Change Detection đang bị gộp logic

Document viết:

> 5 FPS x 1 giờ = 18.000 requests.

Phép tính số frame là đúng, nhưng không đồng nghĩa với 18.000 yêu cầu dịch thuật.

Ví dụ một frame có 10 đoạn chữ, nếu dịch từng đoạn thì chi phí sẽ phụ thuộc vào số đoạn chữ và số lần cache miss, không phải số frame đơn thuần.

Tôi đề xuất có ba tầng:

1. Frame Cache: Nhận diện frame đã xử lý.
    
2. OCR Cache: Lưu kết quả nhận diện.
    
3. Translation Cache: Lưu bản dịch theo text và ngôn ngữ.
    

Khóa cache dịch nên bao gồm:

`hash(source_text + source_language + target_language + provider_version)`

Ngoài ra, nên batch nhiều đoạn text khi provider hỗ trợ.

## 3. Những vấn đề kiến trúc còn thiếu

Đây là các vấn đề chưa được giải quyết đầy đủ trong document.

|Vấn đề|Tại sao quan trọng?|Mức ưu tiên|
|---|---|---|
|Overlay bị capture lại|Có thể tạo vòng lặp ảnh và dịch chính bản dịch|P0|
|Đồng bộ tọa độ|OCR và Overlay có thể lệch vị trí|P0|
|Multi-monitor|Mỗi màn hình có tọa độ và scale khác nhau|P1|
|Fractional scaling|Ảnh capture và tọa độ UI có thể khác đơn vị|P1|
|Xử lý nhiều bong bóng thoại|Cần xác định thứ tự đọc|P1|
|Translation context|Dịch từng câu riêng lẻ dễ sai ngữ cảnh|P1|
|Queue management|Người dùng cuộn nhanh có thể tạo hàng đợi frame cũ|P1|
|Error handling|Mất mạng hoặc OCR lỗi không được làm crash app|P1|

Một vấn đề tôi đặc biệt muốn bạn bổ sung là Frame Queue Management.

Giả sử:

- Capture: 5 FPS.
    
- OCR: 500 ms/frame.
    
- Translation: 700 ms/frame.
    

Nếu cứ xử lý tuần tự toàn bộ frame, hệ thống sẽ ngày càng tụt lại phía sau nội dung thực tế.

Giải pháp nên là ưu tiên frame mới nhất, loại bỏ frame cũ chưa xử lý khi cần thiết và không cho phép cùng một vùng nội dung bị xử lý trùng lặp.

## 4. Kiểm tra Development Roadmap

Roadmap hiện tại chia 5 Phase. Tôi đồng ý với cấu trúc tổng thể, nhưng thứ tự công việc nên thay đổi một chút.

### Vấn đề trong thứ tự hiện tại

Bạn đang để Phase 2 thực hiện OCR, Translation và Inpainting trước khi giải quyết xong Overlay.

Điều này có thể khiến bạn mất nhiều thời gian xây dựng một pipeline hoàn chỉnh nhưng cuối cùng không thể hiển thị kết quả đúng cách trên Niri.

Thứ tự tôi khuyên dùng:

1. Phase 0 — Environment & Feasibility
    
    Bắt buộc trước MVP
    
    - Kiểm tra PipeWire và XDG Portal.
        
    - Kiểm tra capture trên Niri.
        
    - Kiểm tra PySide6 transparent window.
        
    - Kiểm tra click-through.
        
    - Kiểm tra tọa độ màn hình.
        
    
    Output: Các PoC nhỏ chứng minh được những thành phần khó nhất.
    
2. Phase 1 — Image Processing & OCR
    
    - Đọc ảnh từ file.
        
    - Tiền xử lý ảnh.
        
    - PaddleOCR tiếng Hàn.
        
    - Trích xuất text và polygon.
        
    - Đánh giá OCR bằng dataset thực tế.
        
    
    Output: Ảnh đầu vào → danh sách văn bản và tọa độ.
    
3. Phase 2 — Translation & Rendering
    
    - Translation Provider.
        
    - Translation Cache.
        
    - Text grouping.
        
    - OpenCV Inpainting.
        
    - Render tiếng Việt.
        
    
    Output: Ảnh manhwa tiếng Hàn → ảnh đã thay văn bản bằng tiếng Việt.
    
4. Phase 3 — MVP Desktop
    
    - Control Panel.
        
    - Region Selection.
        
    - Screen Capture.
        
    - Overlay.
        
    - Kết nối pipeline.
        
    
    Output: Phần mềm hoạt động trên desktop.
    
5. Phase 4 — Real-time Automation
    
    - Continuous Capture.
        
    - Change Detection.
        
    - Frame Queue.
        
    - Cache Optimization.
        
    - Tối ưu độ trễ.
        
    
    Output: Tự động dịch khi người dùng cuộn truyện.
    
6. Phase 5 — Polish & Portability
    
    - Cải thiện UI/UX.
        
    - Xử lý lỗi.
        
    - Tối ưu tài nguyên.
        
    - Windows compatibility.
        
    - Đóng gói và phát hành.
        
    

Điểm khác biệt: Tôi đưa việc kiểm chứng Overlay và Screen Capture lên trước OCR. Đây là cách giảm rủi ro kỹ thuật và tránh phải viết lại kiến trúc.

### Các tiêu chí kiểm thử cần sửa

Document đặt mục tiêu:

- OCR accuracy trên 90% ở Phase 2.
    
- OCR accuracy trên 95% ở Testing.
    
- Tổng latency dưới 1 giây/frame.
    
- MVP hoàn thành trong dưới 2 giây.
    

Các chỉ tiêu này chưa thống nhất và chưa có điều kiện đo cụ thể.

Tôi đề xuất:

|Chỉ số|Cách đánh giá|
|---|---|
|OCR accuracy|Character Error Rate (CER), Word Error Rate (WER)|
|Translation latency|Đo riêng p50 và p95|
|End-to-end latency|Từ capture đến overlay|
|Frame processing|Số frame xử lý/giây|
|CPU/RAM|Đo khi idle và khi xử lý|
|Overlay alignment|Sai số tọa độ tính bằng pixel|

Đặc biệt, không nên dùng một chỉ số accuracy duy nhất để đánh giá OCR. Với tiếng Hàn, CER rất hữu ích vì một từ có thể gồm nhiều ký tự Hangul.

## 5. Kiểm tra danh sách Task hiện tại

Trong document, bạn đã đánh dấu Task 1.1 là hoàn thành. Các task còn lại đang ở trạng thái chưa thực hiện.

testdoc.md

Tôi đề xuất điều chỉnh danh sách như sau:

|Task|Nội dung|Ưu tiên|
|---|---|---|
|1.1|Setup môi trường|Đã đánh dấu hoàn thành|
|1.2|PoC Screen Capture|P0|
|1.3|PoC Transparent Overlay|P0|
|1.4|PoC Click-through|P0|
|1.5|Kiểm tra tọa độ và scaling|P0|
|2.1|PaddleOCR Korean|P1|
|2.2|OCR polygon và confidence|P1|
|2.3|Translation Provider|P1|
|2.4|SQLite Cache|P1|
|2.5|Text grouping|P1|
|2.6|Inpainting|P2|
|2.7|Vietnamese Text Rendering|P1|
|3.1|Control Panel|P2|
|3.2|Region Selection|P1|
|3.3|Tích hợp Capture và Overlay|P0|
|4.1|Change Detection|P2|
|4.2|Frame Queue|P1|
|4.3|Continuous Capture|P2|

P0: Phải hoàn thành trước khi đi tiếp.  
P1: Chức năng cốt lõi của MVP.  
P2: Có thể hoàn thành sau khi MVP hoạt động.

## 6. Kiểm chứng công nghệ bằng tài liệu chính thức

Tôi đã đối chiếu một số lựa chọn trong document với tài liệu kỹ thuật hiện hành:

|Công nghệ|Kết luận|
|---|---|
|XDG ScreenCast Portal|Phù hợp|
|PipeWire|Phù hợp|
|PaddleOCR|Phù hợp|
|OpenCV Inpainting|Phù hợp có điều kiện|
|PySide6|Cần PoC trên Niri|
|deep-translator|Không nên phụ thuộc lâu dài|
|grim + slurp|Phù hợp PoC|

Nguồn kỹ thuật để bạn tham khảo:

1. [XDG Desktop Portal – ScreenCast](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html?utm_source=chatgpt.com): Quy trình tạo session và nhận PipeWire stream.
    
2. [Niri – Window Rules](https://niri-wm.github.io/niri/Configuration%3A-Window-Rules.html?utm_source=chatgpt.com): Cách compositor quản lý cửa sổ.
    
3. [PaddleOCR – Multilingual Recognition](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html?utm_source=chatgpt.com): Các model và ngôn ngữ được hỗ trợ.
    
4. [XDG Desktop Portal – Remote Desktop](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html?utm_source=chatgpt.com): Quyền điều khiển chuột và bàn phím.
    

Lưu ý: Đây là kiểm chứng ở mức tài liệu và kiến trúc, chưa phải kết quả chạy thử các thư viện trên máy CachyOS của bạn.

## 7. Kết luận và hướng xử lý

Tôi đánh giá document hiện tại có thể giữ lại khoảng 80–85% nội dung, không cần viết lại từ đầu.

Những phần cần sửa chủ yếu là:

1. Technical Research: Làm rõ giới hạn của Wayland/Niri.
    
2. System Architecture: Bổ sung Frame Queue, tọa độ và chống capture vòng lặp.
    
3. Development Roadmap: Đưa PoC Overlay và Capture lên trước.
    
4. Testing Strategy: Chuẩn hóa tiêu chí đo lường.
    
5. MVP: Cho phép hiển thị bản dịch mà không bắt buộc phải xóa chữ gốc.
    

### Tôi đề xuất bước tiếp theo như sau

Khuyến nghị tiếp theo

Tạo Technical Feasibility & PoC Document

Chưa bắt đầu code OCR hoặc Translation. Trước tiên, tạo một document riêng để kiểm chứng 4 vấn đề:

- PoC 1: Capture màn hình bằng PipeWire trên Niri.
    
- PoC 2: Transparent Overlay bằng PySide6.
    
- PoC 3: Click-through và tương tác với ứng dụng bên dưới.
    
- PoC 4: Đồng bộ tọa độ giữa Screen Capture và Overlay.
    

Mỗi PoC cần có mục tiêu, cách thực hiện, kết quả mong đợi, tiêu chí đạt và phương án thay thế.

Một điều tôi muốn nhấn mạnh: Đừng vội xây dựng một ứng dụng dịch truyện hoàn chỉnh. Hãy chứng minh rằng bạn có thể lấy hình ảnh từ màn hình và đặt một lớp dịch chính xác lên trên hình ảnh đó trước.

Đó là nền móng của toàn bộ dự án.