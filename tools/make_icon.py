"""สร้างไอคอน xpass.ico ด้วย Qt (เขียน PNG แล้วประกอบเป็น ICO หลายขนาด)"""
import os
import struct
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPainterPath, QPen

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)

app = QGuiApplication([])


def render(size: int) -> QImage:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)

    # พื้นหลังสี่เหลี่ยมมุมโค้งสีน้ำเงิน
    path = QPainterPath()
    r = size * 0.22
    path.addRoundedRect(QRectF(0, 0, size, size), r, r)
    p.fillPath(path, QColor("#4f7dff"))

    # ตัวอักษร x สีขาว (วาดเป็นเส้น เพื่อให้คมทุกขนาด ไม่พึ่งฟอนต์)
    pen = QPen(QColor("#ffffff"))
    pen.setWidthF(size * 0.135)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    a, b = size * 0.31, size * 0.69
    p.drawLine(QPointF(a, a), QPointF(b, b))
    p.drawLine(QPointF(b, a), QPointF(a, b))

    # จุดสถานะมุมขวาล่าง
    d = size * 0.19
    p.setBrush(QColor("#3fcf7f"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(size - d - size * 0.12, size - d - size * 0.12, d, d))
    p.end()
    return img


sizes = [16, 24, 32, 48, 64, 128, 256]
pngs = []
for s in sizes:
    path = os.path.join(OUT, "xpass_%d.png" % s)
    render(s).save(path, "PNG")
    with open(path, "rb") as fh:
        pngs.append((s, fh.read()))

# ประกอบ ICO (เก็บเป็น PNG ภายใน ซึ่ง Windows Vista+ รองรับ)
header = struct.pack("<HHH", 0, 1, len(pngs))
offset = 6 + 16 * len(pngs)
entries, blobs = b"", b""
for s, data in pngs:
    w = 0 if s >= 256 else s
    entries += struct.pack("<BBBBHHII", w, w, 0, 0, 1, 32, len(data), offset)
    blobs += data
    offset += len(data)

ico_path = os.path.join(OUT, "xpass.ico")
with open(ico_path, "wb") as fh:
    fh.write(header + entries + blobs)
print("เขียนไฟล์:", ico_path, os.path.getsize(ico_path), "bytes")
