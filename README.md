# Real-Time Screen Translator (RTST)

Ứng dụng desktop Python để chọn vùng màn hình, OCR tiếng Hàn, dịch sang tiếng Việt và hiển thị ảnh đã xử lý trên overlay. Ưu tiên CachyOS + Wayland + Niri.

## Trạng thái và giới hạn đã biết

- Có pipeline ảnh file → PaddleOCR adapter → Google Cloud Translation API chính thức → SQLite cache → OpenCV inpainting → Pillow rendering.
- Có capture một lần bằng `slurp` + `grim` để PoC trên Wayland. Đây **không phải** XDG Desktop Portal/PipeWire streaming.
- Có Control Panel PySide6 chạy tác vụ nặng trong `QThreadPool`, chọn vùng, capture, xử lý ảnh và overlay.
- Chưa có backend XDG ScreenCast Portal/PipeWire. Chưa có continuous capture/change detection.
- Transparent/frameless/always-on-top flags được yêu cầu từ Qt, nhưng compositor quyết định hành vi thực tế.
- Click-through không được bật mặc định và chưa được chứng minh trên Niri. Qt `WindowTransparentForInput` có thể bị compositor/backend hạn chế; phương án MVP là Stop/Hide Overlay trước khi thao tác, sau đó chạy dịch lại.
- Tọa độ `slurp`/`grim` và Qt được giả định cùng hệ tọa độ compositor. Fractional scaling, multi-monitor và output transform cần kiểm tra trên máy thật.
- Stop vô hiệu hóa kết quả tác vụ cũ, không thể cưỡng bức ngắt một lệnh OCR/API đang chạy.

## Cài đặt trên CachyOS

```bash
sudo pacman -S --needed python python-pip python-virtualenv grim slurp
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,ocr,vision]"
```

PaddlePaddle/PaddleOCR có thể cần wheel tương thích với Python, CPU/GPU và kiến trúc máy. Nếu cài `.[ocr]` thất bại, kiểm tra ma trận wheel chính thức của PaddlePaddle và cài đúng wheel trước.

## Cấu hình Translation

RTST dùng **Google Cloud Translation API v2 chính thức**, không dùng `deep-translator`.

1. Tạo project Google Cloud, bật Cloud Translation API và cấu hình billing/API key phù hợp.
2. Đặt key trong shell, không ghi vào source code:

```bash
export GOOGLE_CLOUD_TRANSLATE_API_KEY='YOUR_API_KEY'
export RTST_TRANSLATION_TIMEOUT=12
```

Nên giới hạn API key theo API và môi trường sử dụng. Không commit key vào Git.

## Chạy

Giao diện desktop:

```bash
rtst
# hoặc
python -m ocr_overlay
```

Quy trình:
1. Chọn `Select Region`, kéo chọn vùng bằng slurp.
2. Nhấn `Start Translation`.
3. RTST capture một frame, OCR, dịch, xử lý ảnh và mở overlay.
4. Nhấn `Stop / Hide Overlay` để đóng overlay trước khi tương tác với ứng dụng bên dưới.

Debug bằng ảnh file:

```bash
python -m ocr_overlay --image samples/manhwa.png --source ko --target vi --output translated.png
```

Tắt inpainting nếu nền bị hỏng:

```bash
python -m ocr_overlay --image samples/manhwa.png --no-inpaint --output translated.png
```

## Niri / Wayland

- Kiểm tra `echo $XDG_SESSION_TYPE` (mong đợi `wayland`), `which grim slurp`, và portal services.
- `grim`/`slurp` cần compositor hỗ trợ giao thức wlroots screencopy/region selection. Nếu lệnh thất bại, xem backend compositor và portal đang hoạt động.
- Niri quản lý cửa sổ overlay như cửa sổ Wayland thông thường; cấu hình floating rule có thể cần thiết. Không có bảo đảm global always-on-top hay click-through chỉ từ Qt flags.
- Chưa tuyên bố XDG Desktop Portal/PipeWire capture hoàn thành. Để triển khai production cần ScreenCast portal lifecycle (CreateSession → SelectSources → Start → PipeWire node/stream), xử lý quyền người dùng và frame buffer.
- Không dùng `sudo` để chạy ứng dụng GUI.

## Kiểm thử

```bash
pytest -q
```

Các test unit không yêu cầu phiên Wayland, PaddleOCR model hoặc API key. Test capture thật và overlay trên Niri cần chạy thủ công trong desktop session.
