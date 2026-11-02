import sys
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout


def pil_to_qimage(image: Image.Image) -> QImage:
    rgb = image.convert("RGBA")
    data = rgb.tobytes("raw", "RGBA")
    return QImage(data, rgb.width, rgb.height, rgb.width * 4,
                  QImage.Format.Format_RGBA8888).copy()


class Overlay(QWidget):
    """Transparent frameless image overlay positioned in compositor coordinates."""
    def __init__(self, image: Image.Image, x: int, y: int):
        super().__init__()
        self.setWindowTitle("RTST Overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        label = QLabel(self)
        label.setPixmap(QPixmap.fromImage(pil_to_qimage(image)))
        label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        self.setGeometry(x, y, image.width, image.height)


def show_overlay(results):
    app = QApplication.instance() or QApplication(sys.argv)
    from PIL import Image
    from ocr_overlay.vision.processing import render_translations
    width = max((item.box[2] for item in results), default=1)
    height = max((item.box[3] for item in results), default=1)
    base = Image.new("RGB", (max(1, width), max(1, height)), (0, 0, 0))
    rendered = render_translations(base, results)
    overlay = Overlay(rendered, 0, 0)
    overlay.show()
    app.exec()


def show_image_overlay(image: Image.Image, x: int, y: int):
    app = QApplication.instance() or QApplication(sys.argv)
    overlay = Overlay(image, x, y)
    overlay.show()
    app.exec()
