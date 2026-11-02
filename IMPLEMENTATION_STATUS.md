# RTST Implementation Status

## Implemented in this revision

- SQLite translation cache retained.
- OCR model contract retains the existing rectangular `box` API and adds a polygon.
- PaddleOCR 2.x Korean adapter with lazy initialization and legacy OCR output parsing.
- Official Google Cloud Translation API v2 provider with timeout and HTTP/rate-limit error handling.
- `slurp` + `grim` one-shot region capture.
- OpenCV polygon mask/inpainting and Pillow translation rendering.
- PySide6 control panel with worker-thread processing and stale-result suppression.
- Image-file CLI path for debugging.
- Unit tests for cache, OCR parser, translation provider contract, capture region parsing,
  image processing, and pipeline/cache integration.

## Not verified on target desktop

This build was not executed in a CachyOS/Niri graphical session. In this environment,
PySide6 and PaddleOCR are not installed. No live OCR model, Google API request,
grim/slurp invocation, Qt Wayland surface, fractional scaling, or click-through test
was performed.

## Remaining P0/P1 work

1. Implement XDG Desktop Portal ScreenCast + PipeWire frame acquisition (the current
   capture backend is one-shot grim/slurp only).
2. Run the GUI on Niri and verify transparent surface, stacking, focus, and coordinate
   alignment on the user's monitor/scaling configuration.
3. Verify click-through. It is not enabled by default; use Stop/Hide Overlay as the
   current interaction workaround.
4. Validate PaddleOCR model download, Korean recognition quality and PaddleOCR runtime
   compatibility on the target Python/PaddlePaddle environment.
5. Validate a real Google Cloud Translation API key, billing, quotas, timeout and 429
   behavior against the service.
6. Add cancellation tokens for cooperative cancellation inside OCR/translation. Current
   Stop invalidates late results but cannot terminate a running OCR/API operation.
7. Add continuous capture, frame-difference detection and latest-frame queue only after
   the portal and overlay feasibility tests pass.
8. Add tests for real multi-monitor/fractional scaling and OCR CER on a labeled manhwa set.

## Test evidence

- `pytest -q`: 16 passed.
- `python -m compileall -q src`: passed.
- `PYTHONPATH=src python -m ocr_overlay --help`: passed.

Unit tests use mocked translation responses and synthetic images. They do not establish
live service or desktop integration.
