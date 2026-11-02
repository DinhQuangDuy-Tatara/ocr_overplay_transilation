import os
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QVBoxLayout, QWidget, QComboBox, QCheckBox
)

from ocr_overlay.capture.grim import GrimCapture, Region
from ocr_overlay.ocr.paddle_adapter import PaddleOCRAdapter
from ocr_overlay.pipeline.service import OCRTranslationPipeline
from ocr_overlay.storage.cache import TranslationCache
from ocr_overlay.translation.google_cloud import GoogleCloudTranslationProvider
from ocr_overlay.vision.processing import process_translated_image
from ocr_overlay.ui.overlay import Overlay


class WorkerSignals(QObject):
    finished = Signal(int, object, object, str)
    failed = Signal(int, str)


class Task(QRunnable):
    def __init__(self, generation, fn):
        super().__init__()
        self.generation, self.fn = generation, fn
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            image, region = self.fn()
            self.signals.finished.emit(self.generation, image, region, "Hoàn tất")
        except Exception as exc:
            self.signals.failed.emit(self.generation, str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Screen Translator")
        self.resize(420, 220)
        self.pool = QThreadPool.globalInstance()
        self.generation = 0
        self.region = None
        self.overlay = None
        self.capture = GrimCapture()
        self.source = QComboBox()
        self.source.addItem("Korean (ko)", "ko")
        self.target = QComboBox()
        self.target.addItem("Vietnamese (vi)", "vi")
        self.remove_original = QCheckBox("Xóa chữ gốc bằng inpainting")
        self.remove_original.setChecked(True)
        self.status = QLabel("Sẵn sàng. Cần grim + slurp và API key.")
        self.status.setWordWrap(True)
        select_btn = QPushButton("Select Region")
        run_btn = QPushButton("Start Translation")
        stop_btn = QPushButton("Stop / Hide Overlay")
        image_btn = QPushButton("Translate Image…")
        select_btn.clicked.connect(self.select_region)
        run_btn.clicked.connect(self.start_translation)
        stop_btn.clicked.connect(self.stop)
        image_btn.clicked.connect(self.translate_file)
        layout = QVBoxLayout()
        row = QHBoxLayout()
        row.addWidget(QLabel("Nguồn")); row.addWidget(self.source)
        row.addWidget(QLabel("Đích")); row.addWidget(self.target)
        layout.addLayout(row)
        layout.addWidget(self.remove_original)
        for button in (select_btn, run_btn, stop_btn, image_btn):
            layout.addWidget(button)
        layout.addWidget(self.status)
        container = QWidget(); container.setLayout(layout)
        self.setCentralWidget(container)

    def _pipeline(self):
        translator = GoogleCloudTranslationProvider(
            timeout=float(os.getenv("RTST_TRANSLATION_TIMEOUT", "12"))
        )
        cache = TranslationCache(Path.home() / ".cache/rtst/translations.sqlite3")
        return OCRTranslationPipeline(PaddleOCRAdapter(), translator, cache)

    def _submit(self, fn):
        self.generation += 1
        generation = self.generation
        task = Task(generation, fn)
        task.signals.finished.connect(self._on_finished)
        task.signals.failed.connect(self._on_failed)
        self.pool.start(task)
        return generation

    def select_region(self):
        self.status.setText("Đang chờ chọn vùng bằng slurp…")
        def work():
            region = self.capture.select_region()
            return None, region
        self._submit(work)

    def start_translation(self):
        if self.region is None:
            self.status.setText("Hãy Select Region trước.")
            return
        region = self.region
        remove = self.remove_original.isChecked()
        source, target = self.source.currentData(), self.target.currentData()
        self.status.setText("Đang capture → OCR → dịch → render…")
        def work():
            image = self.capture.capture(region)
            lines = self._pipeline().process(image, source, target)
            if not lines:
                raise RuntimeError("OCR không tìm thấy văn bản trong vùng đã chọn.")
            output = process_translated_image(image, lines, remove_original=remove)
            return output, region
        self._submit(work)

    def translate_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh", str(Path.home()), "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if not path:
            return
        remove = self.remove_original.isChecked()
        source, target = self.source.currentData(), self.target.currentData()
        self.status.setText("Đang xử lý ảnh file…")
        def work():
            with Image.open(path) as opened:
                image = opened.convert("RGB")
            lines = self._pipeline().process(image, source, target)
            if not lines:
                raise RuntimeError("OCR không tìm thấy văn bản trong ảnh.")
            return process_translated_image(image, lines, remove_original=remove), Region(0, 0, image.width, image.height)
        self._submit(work)

    @Slot(int, object, object, str)
    def _on_finished(self, generation, image, region, message):
        if generation != self.generation:
            return
        if image is None:
            self.region = region
            self.status.setText(
                f"Đã chọn vùng: {region.x},{region.y} {region.width}x{region.height}"
            )
            return
        self.status.setText(message)
        if self.overlay:
            self.overlay.close()
        self.overlay = Overlay(image, region.x, region.y)
        self.overlay.show()

    @Slot(int, str)
    def _on_failed(self, generation, message):
        if generation == self.generation:
            self.status.setText(f"Lỗi: {message}")

    def stop(self):
        self.generation += 1  # Discard late worker results; cannot interrupt an in-flight OCR/API call.
        if self.overlay:
            self.overlay.close()
            self.overlay = None
        self.status.setText("Đã dừng hiển thị; tác vụ đang chạy sẽ bị bỏ kết quả khi hoàn tất.")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
