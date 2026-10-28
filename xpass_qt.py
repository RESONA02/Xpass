#!/usr/bin/env python3
"""xpass_qt: UI เวอร์ชัน PySide6 (Qt) — ธีมมืดทันสมัย

รัน:  python xpass_qt.py
ต้องมี: pip install PySide6   (และ qrcode ถ้าอยากเห็น QR)

ยังทำงานออฟไลน์ทั้งหมด (ยกเว้นแท็บ “ผู้ช่วย AI”) และเขียนเฉพาะไฟล์ค่าตั้งของผู้ใช้
(ฟอนต์/ขนาด/ปุ่มลัด) — ไม่เก็บรหัสผ่าน TOTP secret หรือ API key ลงดิสก์
ต้องวางไฟล์นี้ไว้โฟลเดอร์เดียวกับ xpass.py
"""
import html
import math
import os
import queue
import re
import secrets
import sys
import threading
import time

from PySide6.QtCore import Qt, QTimer, QSize, Signal, QUrl
from PySide6.QtGui import (
    QAction, QActionGroup, QColor, QDesktopServices, QFont, QGuiApplication, QKeySequence,
    QPainter, QPixmap, QShortcut, QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog, QFontComboBox,
    QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QSizePolicy, QSlider, QSpinBox,
    QStackedWidget, QTextBrowser, QVBoxLayout, QWidget, QScrollArea,
)

try:  # การพิมพ์เป็นออปชัน — ถ้า Qt build ไม่มี PrintSupport แอปยังทำงานปกติ
    from PySide6.QtPrintSupport import QPrintDialog, QPrinter
except Exception:  # pragma: no cover
    QPrintDialog = QPrinter = None

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

try:
    import xpass as core
except Exception as exc:  # pragma: no cover
    raise SystemExit("ต้องวาง xpass_qt.py ไว้ในโฟลเดอร์เดียวกับ xpass.py (%s)" % exc)

import xpass_fonts as appfonts
import xpass_ai as ai
import xpass_settings as appsettings

APP_VERSION = "1.0.1"

# สีข้อความในบทสนทนา AI (ต้องสลับตามธีม เพราะ HTML ไม่ได้ใช้ QSS)
CHAT_COLORS = {
    "dark": {"fg": "#e6e9ef", "user": "#9fb6ff", "ai": "#3fcf7f",
             "muted": "#79828f", "err": "#ff6b7d"},
    "light": {"fg": "#1b2430", "user": "#2f5bd0", "ai": "#128a4d",
              "muted": "#6b7686", "err": "#d92d4a"},
}

QSS = """
QWidget { color: #e6e9ef; font-family: "__UI__"; font-size: 13px; }
#Root { background: #0b0d10; }
#Sidebar { background: #0e1116; border-right: 1px solid #1a212c; }
#Brand { font-size: 24px; font-weight: 700; letter-spacing: 0.5px; }
#BrandSub { color: #79828f; font-size: 11px; }
#H1 { font-size: 21px; font-weight: 700; }
#H2 { font-size: 14px; font-weight: 600; }
#Muted { color: #79828f; font-size: 12px; }
#Err { color: #ff6b7d; font-size: 12px; }
#Ok { color: #3fcf7f; font-size: 12px; }
#Mono { font-family: "__MONO__"; font-size: 13px; }
#Big { font-family: "__MONO__"; font-size: 54px; font-weight: 700; letter-spacing: 4px; }
#Badge { background: #1b2333; border-radius: 8px; padding: 3px 10px; font-weight: 600; color: #9fb6ff; }
#Warn { color: #ffc46b; background: #241d10; border: 1px solid #3a2d15; border-radius: 10px;
        padding: 9px 12px; font-size: 12px; }
#Chat { background: #0d1117; border: 1px solid #222b38; border-radius: 9px;
        font-size: 13px; padding: 6px 8px; }

QFrame#Card { background: #11151c; border: 1px solid #1d2430; border-radius: 14px; }

QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }

QPushButton { background: #1a212c; border: 1px solid #26303f; border-radius: 9px;
              padding: 8px 14px; color: #d6dbe6; font-weight: 500; }
QPushButton:hover { background: #232d3b; border-color: #334052; }
QPushButton:pressed { background: #1d2530; }

QPushButton#Nav { text-align: left; padding: 11px 14px; border: none; border-radius: 10px;
                  background: transparent; color: #98a1b0; font-size: 13px; font-weight: 400; }
QPushButton#Nav:hover { background: #161c26; color: #e6e9ef; }
QPushButton#Nav:checked { background: #1a2436; color: #ffffff; font-weight: 600; }

QPushButton#Primary { background: #4f7dff; border: none; color: #ffffff; font-weight: 600; }
QPushButton#Primary:hover { background: #6a92ff; }
QPushButton#Primary:pressed { background: #3f66d6; }

QPushButton#Ghost { background: transparent; border: 1px solid #26303f; }

QLineEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background: #0d1117; border: 1px solid #222b38; border-radius: 9px;
    padding: 8px 10px; selection-background-color: #2f5bd0; color: #e6e9ef;
}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus,
QComboBox:on { border: 1px solid #4f7dff; }
QLineEdit[readOnly="true"] { color: #b9c2d0; }
QPlainTextEdit { font-family: "__MONO__"; font-size: 14px; }

QComboBox::drop-down { border: none; width: 26px; }
QComboBox::down-arrow { image: none; margin-right: 9px;
                        border-left: 4px solid transparent; border-right: 4px solid transparent;
                        border-top: 5px solid #98a1b0; }
QComboBox QAbstractItemView { background: #0d1117; border: 1px solid #222b38;
                              selection-background-color: #1a2436; selection-color: #ffffff;
                              outline: none; padding: 4px; }
QComboBox QLineEdit { border: none; background: transparent; padding: 0; }

QCheckBox { spacing: 9px; color: #cdd4e0; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 5px;
                       border: 1px solid #39445a; background: #0d1117; }
QCheckBox::indicator:checked { background: #4f7dff; border-color: #4f7dff; }

QSlider::groove:horizontal { height: 6px; background: #1b2330; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #4f7dff; border-radius: 3px; }
QSlider::handle:horizontal { width: 16px; height: 16px; margin: -6px 0;
                             border-radius: 8px; background: #ffffff; }

QProgressBar { background: #151b24; border: none; border-radius: 5px; height: 10px; }
QProgressBar::chunk { background: #3fcf7f; border-radius: 5px; }

QSpinBox::up-button, QSpinBox::down-button { width: 0; border: none; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #2b3648; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #3a4760; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: #2b3648; border-radius: 5px; min-width: 24px; }
QScrollBar::handle:horizontal:hover { background: #3a4760; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; border: none; background: none; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QMenuBar { background: #0e1116; border-bottom: 1px solid #1a212c; padding: 2px 6px; }
QMenuBar::item { background: transparent; padding: 5px 10px; border-radius: 6px; color: #e6e9ef; }
QMenuBar::item:selected, QMenuBar::item:pressed { background: #1a2436; color: #ffffff; }
QMenu { background: #11151c; border: 1px solid #222b38; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 7px 28px 7px 26px; border-radius: 6px; color: #e6e9ef; }
QMenu::item:selected { background: #1a2436; color: #ffffff; }
QMenu::item:disabled { color: #5b6472; }
QMenu::separator { height: 1px; background: #1d2430; margin: 5px 8px; }
QMenu::indicator { width: 14px; height: 14px; margin-left: 8px; }

#Toast { background: #11151c; border: 1px solid #26303f; border-radius: 8px;
         padding: 8px 14px; color: #d6dbe6; font-size: 12px; }

QDialog, QMessageBox, QInputDialog { background: #0b0d10; }
QDialog QLabel, QMessageBox QLabel, QInputDialog QLabel { color: #e6e9ef; }
QDialog QLineEdit { background: #0d1117; }
"""

_FONT_SIZE_RE = re.compile(r"font-size:\s*(\d+)px")

# แปลงสีของ QSS ธีมมืด → ธีมสว่าง (จับคู่ทีละสี เพื่อไม่ต้องเขียน QSS ซ้ำทั้งชุด)
_LIGHT_COLORS = {
    "#e6e9ef": "#1b2430",
    "#0b0d10": "#f4f6fa",
    "#0e1116": "#ffffff",
    "#1a212c": "#e2e6ef",
    "#79828f": "#6b7686",
    "#ff6b7d": "#d92d4a",
    "#3fcf7f": "#128a4d",
    "#1b2333": "#e7edfb",
    "#9fb6ff": "#2f5bd0",
    "#ffc46b": "#9a6100",
    "#241d10": "#fff6e0",
    "#3a2d15": "#f0d9a8",
    "#0d1117": "#ffffff",
    "#222b38": "#d7dde8",
    "#2f5bd0": "#3f6fe0",
    "#11151c": "#ffffff",
    "#1d2430": "#e5e9f1",
    "#26303f": "#d3dae6",
    "#d6dbe6": "#2c3644",
    "#232d3b": "#eef2f8",
    "#334052": "#c3cddb",
    "#1d2530": "#e6ebf3",
    "#98a1b0": "#5b6675",
    "#161c26": "#eef2f8",
    "#1a2436": "#e3ebfb",
    "#39445a": "#b8c2d2",
    "#1b2330": "#e3e8f1",
    "#151b24": "#e8ecf3",
    "#2b3648": "#c9d1de",
    "#3a4760": "#aab6c8",
    "#b9c2d0": "#5b6675",
    "#cdd4e0": "#2c3644",
    "#5b6472": "#9aa4b2",
}

_LIGHT_OVERRIDES = """
QPushButton#Nav:checked { color: #12203a; }
QMenuBar::item:selected, QMenuBar::item:pressed { color: #12203a; }
QMenu::item:selected { color: #12203a; }
QComboBox QAbstractItemView { selection-color: #12203a; }
"""


def build_qss(ui_family, mono_family, scale=1.0, theme="dark"):
    """สร้าง QSS ตามฟอนต์/ขนาด/ธีมที่ผู้ใช้เลือก (ขนาดใน QSS เป็น px)"""
    try:
        scale = max(0.8, min(1.5, float(scale)))
    except (TypeError, ValueError):
        scale = 1.0

    def _scale_size(match):
        size = int(round(int(match.group(1)) * scale))
        return "font-size: %dpx" % max(8, size)

    qss = (_FONT_SIZE_RE.sub(_scale_size, QSS)
           .replace("__UI__", ui_family)
           .replace("__MONO__", mono_family))
    if theme == "light":
        for dark, light in _LIGHT_COLORS.items():
            qss = qss.replace(dark, light)
        qss += _LIGHT_OVERRIDES
    return qss


def card(title=None, subtitle=None):
    frame = QFrame()
    frame.setObjectName("Card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(18, 16, 18, 18)
    lay.setSpacing(10)
    if title:
        lb = QLabel(title)
        lb.setObjectName("H2")
        lb.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        lay.addWidget(lb)
    if subtitle:
        sb = QLabel(subtitle)
        sb.setObjectName("Muted")
        sb.setWordWrap(True)
        sb.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        lay.addWidget(sb)
    frame.body = lay
    return frame


def muted(text):
    lb = QLabel(text)
    lb.setObjectName("Muted")
    lb.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    return lb


def hline():
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet("background: #1b222d; border: none;")
    return line


class BasePage(QWidget):
    def __init__(self, title, subtitle):
        super().__init__()
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(26, 22, 26, 22)
        self.root.setSpacing(14)
        head = QLabel(title)
        head.setObjectName("H1")
        self.root.addWidget(head)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("Muted")
            sub.setWordWrap(True)
            self.root.addWidget(sub)

    def flash(self, btn, text="คัดลอกแล้ว ✓"):
        old = btn.text()
        btn.setText(text)
        btn.setEnabled(False)
        QTimer.singleShot(1100, lambda: (btn.setText(old), btn.setEnabled(True)))

    def copy(self, text, btn=None):
        text = (text or "").strip()
        if not text:
            return
        QGuiApplication.clipboard().setText(text)
        if btn is not None:
            self.flash(btn)

    def export_text(self):
        """ข้อความของแท็บนี้สำหรับบันทึก/พิมพ์/ส่งออก (ค่าเริ่มต้น: ไม่มี)"""
        return ""


# --------------------------------------------------------------- รหัสผ่าน
class PasswordPage(BasePage):
    def __init__(self):
        super().__init__("สร้างรหัสผ่าน", "สุ่มด้วย secrets ของระบบปฏิบัติการ — คาดเดาไม่ได้ และไม่ถูกบันทึกที่ไหน")

        form = card("ตัวเลือก")
        row = QHBoxLayout()
        row.addWidget(QLabel("ความยาว"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(8, 64)
        self.slider.setValue(20)
        row.addWidget(self.slider, 1)
        self.len_badge = QLabel("20")
        self.len_badge.setObjectName("Badge")
        self.len_badge.setAlignment(Qt.AlignCenter)
        self.len_badge.setFixedWidth(46)
        row.addWidget(self.len_badge)
        form.body.addLayout(row)
        self.slider.valueChanged.connect(lambda v: self.len_badge.setText(str(v)))

        opts = QHBoxLayout()
        self.cb_sym = QCheckBox("ใส่สัญลักษณ์  !@#$…")
        self.cb_sym.setChecked(True)
        self.cb_amb = QCheckBox("ตัดตัวที่อ่านสับสน  Il1O0o")
        opts.addWidget(self.cb_sym)
        opts.addWidget(self.cb_amb)
        opts.addStretch(1)
        opts.addWidget(QLabel("จำนวน"))
        self.count = QSpinBox()
        self.count.setRange(1, 20)
        self.count.setSuffix(" ชุด")
        self.count.setAlignment(Qt.AlignRight)
        self.count.setFixedWidth(96)
        opts.addWidget(self.count)
        form.body.addLayout(opts)

        self.btn_gen = QPushButton("สร้างรหัสผ่าน")
        self.btn_gen.setObjectName("Primary")
        self.btn_gen.setMinimumHeight(38)
        form.body.addWidget(self.btn_gen)
        self.root.addWidget(form)

        out = card("ผลลัพธ์")
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setMinimumHeight(150)
        self.text.setPlaceholderText("กด “สร้างรหัสผ่าน” เพื่อเริ่ม")
        out.body.addWidget(self.text)
        tools = QHBoxLayout()
        self.btn_copy_all = QPushButton("คัดลอกทั้งหมด")
        self.btn_clear = QPushButton("ล้าง")
        self.btn_clear.setObjectName("Ghost")
        self.bits = muted("")
        tools.addWidget(self.btn_copy_all)
        tools.addWidget(self.btn_clear)
        tools.addStretch(1)
        tools.addWidget(self.bits)
        out.body.addLayout(tools)
        self.root.addWidget(out, 1)

        self.btn_gen.clicked.connect(self.generate)
        self.btn_copy_all.clicked.connect(lambda: self.copy(self.text.toPlainText(), self.btn_copy_all))
        self.btn_clear.clicked.connect(lambda: (self.text.clear(), self.bits.setText("")))
        self.auto_copy = False

    def apply_settings(self, settings):
        self.auto_copy = bool(settings.get("auto_copy", False))

    def generate(self):
        length, count = self.slider.value(), self.count.value()
        symbols, no_ambig = self.cb_sym.isChecked(), self.cb_amb.isChecked()
        lines, bits = [], 0.0
        for _ in range(count):
            p, bits = core.gen_password(length, symbols, no_ambig)
            lines.append(p)
        self.text.setPlainText("\n".join(lines))
        self.bits.setText("ประมาณ %d บิต entropy" % bits)
        if self.auto_copy:
            self.copy(self.text.toPlainText(), self.btn_copy_all)

    def export_text(self):
        return self.text.toPlainText().strip()


# ------------------------------------------------------------- ชื่อหน้าลับ
class NamePage(BasePage):
    def __init__(self):
        super().__init__("ชื่อหน้าลับ", "สร้างชื่อไฟล์ / URL ที่คาดเดายาก กันคนกวาดหา path")

        form = card("ตั้งค่า")
        row = QHBoxLayout()
        row.addWidget(QLabel("ความยาว"))
        self.spin = QSpinBox()
        self.spin.setRange(8, 64)
        self.spin.setValue(24)
        self.spin.setSuffix(" ตัว")
        self.spin.setAlignment(Qt.AlignRight)
        self.spin.setFixedWidth(96)
        row.addWidget(self.spin)
        row.addSpacing(18)
        row.addWidget(QLabel("คำนำหน้า"))
        self.prefix = QLineEdit("a-")
        self.prefix.setFixedWidth(110)
        row.addWidget(self.prefix)
        row.addStretch(1)
        form.body.addLayout(row)
        self.btn_gen = QPushButton("สร้างชื่อ")
        self.btn_gen.setObjectName("Primary")
        self.btn_gen.setMinimumHeight(38)
        form.body.addWidget(self.btn_gen)
        self.root.addWidget(form)

        out = card("ผลลัพธ์")
        self.output = QLineEdit()
        self.output.setReadOnly(True)
        self.output.setObjectName("Mono")
        self.output.setPlaceholderText("ยังไม่มีชื่อ")
        self.output.setMinimumHeight(40)
        out.body.addWidget(self.output)
        tools = QHBoxLayout()
        self.btn_copy = QPushButton("คัดลอก")
        self.bits = muted("")
        tools.addWidget(self.btn_copy)
        tools.addStretch(1)
        tools.addWidget(self.bits)
        out.body.addLayout(tools)
        self.root.addWidget(out)
        self.root.addStretch(1)

        self.btn_gen.clicked.connect(self.generate)
        self.btn_copy.clicked.connect(lambda: self.copy(self.output.text(), self.btn_copy))

    def generate(self):
        n = self.spin.value()
        page = "%s%s.html" % (self.prefix.text().strip(), core.gen_slug(n))
        self.output.setText(page)
        self.bits.setText("ประมาณ %d บิต entropy" % (n * math.log2(36)))

    def export_text(self):
        return self.output.text().strip()


# ---------------------------------------------------------- ชุดค่า admin
class AdminPage(BasePage):
    FIELD_LABELS = (("token", "ADMIN_TOKEN"), ("secret", "ADMIN_TOTP_SECRET"),
                    ("page", "ชื่อหน้า admin ลับ"), ("uri", "ลิงก์ otpauth"))

    def __init__(self):
        super().__init__("ชุดค่า admin", "สร้าง token, secret 2FA และชื่อหน้าลับสำหรับ Cloudflare Worker — แสดงครั้งเดียว ไม่บันทึกลงดิสก์")
        self.theme = "dark"

        body = QHBoxLayout()
        body.setSpacing(14)

        left = QVBoxLayout()
        left.setSpacing(14)
        form = card("การตั้งค่า")
        row = QHBoxLayout()
        row.addWidget(QLabel("Issuer"))
        self.issuer = QLineEdit("XRay Admin")
        row.addWidget(self.issuer, 1)
        row.addSpacing(10)
        row.addWidget(QLabel("บัญชี"))
        self.account = QLineEdit("admin")
        self.account.setFixedWidth(130)
        row.addWidget(self.account)
        form.body.addLayout(row)
        self.btn_gen = QPushButton("สร้างชุดค่า admin")
        self.btn_gen.setObjectName("Primary")
        self.btn_gen.setMinimumHeight(38)
        form.body.addWidget(self.btn_gen)
        left.addWidget(form)

        values = card("ค่าที่ได้")
        self.fields = {}
        for key, label in self.FIELD_LABELS:
            values.body.addWidget(muted(label))
            line = QHBoxLayout()
            edit = QLineEdit()
            edit.setReadOnly(True)
            edit.setObjectName("Mono")
            edit.setMinimumHeight(36)
            copy_btn = QPushButton("คัดลอก")
            copy_btn.setFixedWidth(84)
            copy_btn.clicked.connect(lambda _=False, e=edit, b=copy_btn: self.copy(e.text(), b))
            line.addWidget(edit, 1)
            line.addWidget(copy_btn)
            values.body.addLayout(line)
            self.fields[key] = edit
        self.note = QLabel("ค่าจะถูกสร้างใหม่ทุกครั้งที่กดปุ่ม")
        self.note.setObjectName("Muted")
        self.note.setWordWrap(True)
        values.body.addWidget(self.note)
        left.addWidget(values)
        left.addStretch(1)
        body.addLayout(left, 1)

        qr_card = card("สแกนด้วยแอป Authenticator")
        self.qr = QLabel("กด “สร้างชุดค่า admin”\nเพื่อแสดง QR")
        self.qr.setAlignment(Qt.AlignCenter)
        self.qr.setFixedSize(296, 296)
        self.qr.setStyleSheet("background: #0d1117; border: 1px solid #1d2430; border-radius: 12px;")
        self.qr.setWordWrap(True)
        self.btn_qr = QPushButton("แสดง QR ใหม่")
        self.btn_qr.setObjectName("Ghost")
        qr_card.body.addStretch(1)
        qr_card.body.addWidget(self.qr, 0, Qt.AlignHCenter)
        qr_card.body.addStretch(1)
        qr_card.body.addSpacing(4)
        qr_card.body.addWidget(self.btn_qr)
        body.addWidget(qr_card, 0)

        self.root.addLayout(body, 1)

        self.btn_gen.clicked.connect(self.generate)
        self.btn_qr.clicked.connect(self.redraw_qr)
        self._uri = ""

    def apply_settings(self, settings):
        self.theme = "light" if settings.get("theme") == "light" else "dark"
        if self.theme == "light":
            self.qr.setStyleSheet("background: #ffffff; border: 1px solid #d7dde8; border-radius: 12px;")
        else:
            self.qr.setStyleSheet("background: #0d1117; border: 1px solid #1d2430; border-radius: 12px;")
        if any(edit.text().strip() for edit in self.fields.values()):
            self.note.setStyleSheet("color: %s; font-size: 12px;" % self._note_color())

    def _note_color(self):
        return "#128a4d" if self.theme == "light" else "#3fcf7f"

    def generate(self):
        issuer = self.issuer.text().strip() or "XRay Admin"
        account = self.account.text().strip() or "admin"
        token = core.gen_alnum(40)
        secret = core.b32enc(secrets.token_bytes(20))
        page = "a-%s.html" % core.gen_slug(24)
        uri = core.otpauth_uri(secret, issuer, account)
        code = core.totp(core.b32dec(secret), int(time.time()) // 30)

        self.fields["token"].setText(token)
        self.fields["secret"].setText(secret)
        self.fields["page"].setText(page)
        self.fields["uri"].setText(uri)
        self._uri = uri
        self.draw_qr(uri)
        self.note.setObjectName("Ok")
        self.note.setStyleSheet("color: %s; font-size: 12px;" % self._note_color())
        self.note.setText("รหัสตอนนี้ควรตรงกับแอป: %s %s" % (code[:3], code[3:]))

    def export_text(self):
        lines = []
        for key, label in self.FIELD_LABELS:
            value = self.fields[key].text().strip()
            if value:
                lines.append("%s: %s" % (label, value))
        return "\n".join(lines)

    def redraw_qr(self):
        if not self._uri:
            self.qr.setText("กด “สร้างชุดค่า admin” ก่อน")
            return
        self.draw_qr(self._uri)

    def draw_qr(self, data):
        try:
            import qrcode
        except ImportError:
            self.qr.setPixmap(QPixmap())
            self.qr.setText("ไม่มีไลบรารี qrcode\npip install qrcode\nหรือคัดลอกลิงก์ otpauth ไปสร้าง QR เอง")
            return
        q = qrcode.QRCode(border=2, box_size=1)
        q.add_data(data)
        q.make()
        matrix = q.get_matrix()
        n = len(matrix)
        scale = max(2, 276 // n)
        size = n * scale
        pm = QPixmap(size, size)
        pm.fill(QColor("#ffffff"))
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, False)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#0b0d10"))
        for y, row in enumerate(matrix):
            for x, on in enumerate(row):
                if on:
                    p.drawRect(x * scale, y * scale, scale, scale)
        p.end()
        self.qr.setText("")
        self.qr.setPixmap(pm)


# ------------------------------------------------------------- TOTP สด
class TotpPage(BasePage):
    def __init__(self):
        super().__init__("รหัส TOTP สด", "ใส่ secret (base32) เพื่อดูรหัส 6 หลักแบบออฟไลน์")

        form = card("Secret")
        row = QHBoxLayout()
        self.secret = QLineEdit(os.environ.get("XPASS_SECRET", ""))
        self.secret.setPlaceholderText("เช่น JBSWY3DPEHPK3PXP")
        self.secret.setObjectName("Mono")
        self.secret.setEchoMode(QLineEdit.Password)
        self.secret.setMinimumHeight(38)
        row.addWidget(self.secret, 1)
        self.btn_eye = QPushButton("แสดง")
        self.btn_eye.setObjectName("Ghost")
        self.btn_eye.setFixedWidth(74)
        row.addWidget(self.btn_eye)
        self.btn_run = QPushButton("เริ่ม")
        self.btn_run.setObjectName("Primary")
        self.btn_run.setFixedWidth(96)
        row.addWidget(self.btn_run)
        form.body.addLayout(row)
        self.err = QLabel("")
        self.err.setObjectName("Err")
        form.body.addWidget(self.err)
        self.root.addWidget(form)

        center = card()
        center.body.addStretch(1)
        self.code = QLabel("••• •••")
        self.code.setObjectName("Big")
        self.code.setAlignment(Qt.AlignCenter)
        center.body.addWidget(self.code)
        self.bar = QProgressBar()
        self.bar.setRange(0, 30)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(10)
        center.body.addWidget(self.bar)
        self.sub = muted("ใส่ secret แล้วกด “เริ่ม”")
        self.sub.setAlignment(Qt.AlignCenter)
        center.body.addWidget(self.sub)
        self.btn_copy = QPushButton("คัดลอกรหัส")
        self.btn_copy.setObjectName("Ghost")
        self.btn_copy.setFixedWidth(170)
        center.body.addSpacing(16)
        center.body.addWidget(self.btn_copy, 0, Qt.AlignHCenter)
        center.body.addStretch(1)
        self.root.addWidget(center, 1)

        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.tick)
        self._key = None
        self._code = ""

        self.btn_eye.clicked.connect(self.toggle_eye)
        self.btn_run.clicked.connect(self.toggle)
        self.btn_copy.clicked.connect(lambda: self.copy(self._code, self.btn_copy))
        self.secret.returnPressed.connect(self.toggle)

    def toggle_eye(self):
        hidden = self.secret.echoMode() == QLineEdit.Password
        self.secret.setEchoMode(QLineEdit.Normal if hidden else QLineEdit.Password)
        self.btn_eye.setText("ซ่อน" if hidden else "แสดง")

    def toggle(self):
        if self.timer.isActive():
            self.timer.stop()
            self._key = None
            self._code = ""
            self.code.setText("••• •••")
            self.bar.setValue(0)
            self.sub.setText("หยุดแล้ว")
            self.btn_run.setText("เริ่ม")
            return
        raw = self.secret.text().strip()
        if not raw:
            self.err.setText("ใส่ secret ก่อนครับ")
            self.secret.setFocus()
            return
        try:
            key = core.b32dec(raw)
            if not key:
                raise ValueError
        except Exception:
            self.err.setText("secret ไม่ถูกต้อง — ต้องเป็นตัวอักษร A–Z และเลข 2–7 (base32)")
            return
        self.err.setText("")
        self._key = key
        self.btn_run.setText("หยุด")
        self.secret.setEchoMode(QLineEdit.Password)
        self.btn_eye.setText("แสดง")
        self.timer.start()
        self.tick()

    def tick(self):
        now = int(time.time())
        left = 30 - now % 30
        self._code = core.totp(self._key, now // 30)
        self.code.setText("%s %s" % (self._code[:3], self._code[3:]))
        self.bar.setValue(left)
        self.sub.setText("เหลืออีก %d วินาที" % left)

    def export_text(self):
        if not self._code:
            return ""
        return "TOTP: %s\nเหลืออีก %d วินาที" % (self._code, 30 - int(time.time()) % 30)


# ------------------------------------------------------------- ผู้ช่วย AI
class ChatInput(QPlainTextEdit):
    """ช่องพิมพ์แชท — Enter/Ctrl+Enter เพื่อส่ง ตามค่าตั้งในหน้า “ตั้งค่า”"""

    sendRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.send_mode = "ctrl+enter"

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            mods = event.modifiers()
            if self.send_mode == "enter":
                if not (mods & Qt.ShiftModifier):
                    self.sendRequested.emit()
                    return
            elif mods & Qt.ControlModifier:
                self.sendRequested.emit()
                return
        super().keyPressEvent(event)


class AiPage(BasePage):
    def __init__(self, default_model=None):
        super().__init__("ผู้ช่วย AI", "ถามเรื่องรหัสผ่าน 2FA และความปลอดภัยได้ — แท็บนี้เชื่อมต่ออินเทอร์เน็ต")
        self.confirm_clear = True
        self.remember_model = True
        self.theme = "dark"
        self.on_model = None  # callback(model) — ให้หน้าต่างหลักจำโมเดลล่าสุด

        warn = QLabel("คำเตือน: อย่าพิมพ์รหัสผ่านจริง TOTP secret หรือ API key ลงในช่องแชท — ข้อความจะถูกส่งไปยังผู้ให้บริการ AI (OpenAI หรือ Google Gemini)")
        warn.setObjectName("Warn")
        warn.setWordWrap(True)
        self.root.addWidget(warn)

        cfg = card("การเชื่อมต่อ")
        row = QHBoxLayout()
        row.addWidget(QLabel("API key"))
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.Password)
        self.key.setObjectName("Mono")
        self.key.setPlaceholderText("sk-... / AIza...")
        self.key.setMinimumHeight(36)
        row.addWidget(self.key, 1)
        self.btn_eye = QPushButton("แสดง")
        self.btn_eye.setObjectName("Ghost")
        self.btn_eye.setFixedWidth(74)
        row.addWidget(self.btn_eye)
        row.addSpacing(14)
        row.addWidget(QLabel("โมเดล"))
        self.model = QComboBox()
        self.model.setObjectName("Mono")
        self.model.setEditable(True)
        self.model.addItems(list(ai.MODEL_CHOICES))
        self.model.setCurrentText((default_model or "").strip() or ai.default_model())
        self.model.setFixedWidth(220)
        self.model.setMinimumHeight(36)
        self.model.setToolTip("เลือกจากรายการ หรือพิมพ์ชื่อโมเดลอื่นเองก็ได้\n"
                              "gemini… = Google Gemini, gpt… = OpenAI")
        row.addWidget(self.model)
        self.btn_refresh = QPushButton("รีเฟรช")
        self.btn_refresh.setObjectName("Ghost")
        self.btn_refresh.setFixedWidth(84)
        self.btn_refresh.setMinimumHeight(36)
        self.btn_refresh.setToolTip("ดึงรายการโมเดลที่ API key นี้ใช้ได้จริง")
        row.addWidget(self.btn_refresh)
        cfg.body.addLayout(row)
        self.key_hint = muted("")
        cfg.body.addWidget(self.key_hint)
        self._update_hint()
        self.root.addWidget(cfg)

        chat_card = card("บทสนทนา")
        self.view = QTextBrowser()
        self.view.setObjectName("Chat")
        self.view.setMinimumHeight(170)
        self.view.setOpenExternalLinks(False)
        chat_card.body.addWidget(self.view, 1)

        self.input = ChatInput()
        self.input.setPlaceholderText("พิมพ์คำถาม เช่น “TOTP ต่างจากรหัสผ่านอย่างไร”   (Ctrl+Enter เพื่อส่ง)")
        self.input.setFixedHeight(74)
        chat_card.body.addWidget(self.input)

        bottom = QHBoxLayout()
        self.btn_send = QPushButton("ส่งคำถาม")
        self.btn_send.setObjectName("Primary")
        self.btn_send.setMinimumHeight(36)
        self.btn_clear = QPushButton("ล้างบทสนทนา")
        self.btn_clear.setObjectName("Ghost")
        self.status = muted("")
        bottom.addWidget(self.btn_send)
        bottom.addWidget(self.btn_clear)
        bottom.addStretch(1)
        bottom.addWidget(self.status)
        chat_card.body.addLayout(bottom)
        self.root.addWidget(chat_card, 1)

        self.messages = [{"role": "system", "content": ai.SYSTEM_PROMPT}]
        self._queue = queue.Queue()
        self._busy = False
        self._timer = QTimer(self)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._poll)

        self._append(None, self._hint_text(), self._colors()["muted"])

        self.btn_send.clicked.connect(self.send)
        self.btn_clear.clicked.connect(self.clear_chat)
        self.btn_eye.clicked.connect(self.toggle_eye)
        self.btn_refresh.clicked.connect(self.refresh_models)
        self.input.sendRequested.connect(self.send)
        self.model.currentTextChanged.connect(self._update_hint)

    def _current_model(self):
        return self.model.currentText().strip() or ai.default_model()

    def apply_settings(self, settings):
        """รับค่าตั้งจากหน้าต่างหลัก (ปุ่มส่ง, ยืนยันล้างแชท, จำโมเดล, ธีม)"""
        self.confirm_clear = bool(settings.get("confirm_clear", True))
        self.remember_model = bool(settings.get("remember_model", True))
        theme = "light" if settings.get("theme") == "light" else "dark"
        if theme != self.theme:
            self.theme = theme
            self._render_history()
        mode = settings.get("send_key", "ctrl+enter")
        self.input.send_mode = mode if mode in ("ctrl+enter", "enter") else "ctrl+enter"
        if self.input.send_mode == "enter":
            self.input.setPlaceholderText("พิมพ์คำถาม เช่น “TOTP ต่างจากรหัสผ่านอย่างไร”   "
                                          "(Enter เพื่อส่ง, Shift+Enter ขึ้นบรรทัดใหม่)")
        else:
            self.input.setPlaceholderText("พิมพ์คำถาม เช่น “TOTP ต่างจากรหัสผ่านอย่างไร”   "
                                          "(Ctrl+Enter เพื่อส่ง)")

    def _colors(self):
        return CHAT_COLORS.get(self.theme, CHAT_COLORS["dark"])

    def _hint_text(self):
        return "ถามได้เลย เช่น “TOTP ต่างจากรหัสผ่านอย่างไร” หรือ “ควรเก็บ secret 2FA ที่ไหน”"

    def _render_history(self):
        """วาดบทสนทนาใหม่ด้วยสีของธีมปัจจุบัน (สลับมืด/สว่างแล้วยังอ่านได้)"""
        self.view.clear()
        colors = self._colors()
        if len(self.messages) <= 1:
            self._append(None, self._hint_text(), colors["muted"])
            return
        for message in self.messages[1:]:
            if message.get("role") == "user":
                self._append("คุณ", message.get("content", ""), colors["user"])
            elif message.get("role") == "assistant":
                self._append("AI", message.get("content", ""), colors["ai"])

    def _update_hint(self):
        provider = ai.provider_for_model(self._current_model())
        env_name = ai.env_key_name(provider)
        if env_name:
            self.key_hint.setText("ใช้คีย์จาก %s ในเครื่อง (ไม่ต้องพิมพ์ซ้ำ)" % env_name)
        else:
            self.key_hint.setText("คีย์จะอยู่ในหน่วยความจำเท่านั้น ไม่ถูกบันทึกลงดิสก์ · %s"
                                  % ai.provider_label(provider))

    def toggle_eye(self):
        hidden = self.key.echoMode() == QLineEdit.Password
        self.key.setEchoMode(QLineEdit.Normal if hidden else QLineEdit.Password)
        self.btn_eye.setText("ซ่อน" if hidden else "แสดง")

    def _append(self, who, text, color=None):
        colors = self._colors()
        color = color or colors["fg"]
        body = html.escape(text).replace("\n", "<br>")
        if who:
            block = ('<div style="margin:8px 0"><span style="color:%s;font-weight:600">%s</span>'
                     '<br><span style="color:%s">%s</span></div>'
                     % (color, html.escape(who), colors["fg"], body))
        else:
            block = '<div style="margin:8px 0;color:%s">%s</div>' % (color, body)
        self.view.append(block)
        bar = self.view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def send(self):
        if self._busy:
            return
        text = self.input.toPlainText().strip()
        if not text:
            self.input.setFocus()
            return

        model = self._current_model()
        provider = ai.provider_for_model(model)
        if self.remember_model and self.on_model is not None:
            self.on_model(model)

        key = self.key.text().strip() or ai.env_api_key(provider)
        if not key:
            self._append(None, "ผิดพลาด: ยังไม่มี API key ของ %s — ใส่คีย์ด้านบนหรือตั้งค่า %s"
                         % (ai.provider_label(provider), " / ".join(ai.PROVIDER_ENV_KEYS[provider])),
                         self._colors()["err"])
            self.key.setFocus()
            return

        self.input.clear()
        self.messages.append({"role": "user", "content": text})
        self._append("คุณ", text, self._colors()["user"])

        self._busy = True
        self.btn_send.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.status.setText("กำลังคิด…")
        snapshot = self._context()
        threading.Thread(target=self._worker,
                         args=(snapshot, key, model, provider), daemon=True).start()
        self._timer.start()

    def _context(self, limit=12):
        """ส่งเฉพาะบทสนทนาล่าสุด เพื่อคุมจำนวน token"""
        system = [self.messages[0]] if self.messages else []
        rest = [m for m in self.messages[1:] if m.get("role") in ("user", "assistant")]
        return system + rest[-limit:]

    def _worker(self, messages, key, model, provider):
        try:
            reply = ai.chat(messages, key=key, model=model, provider=provider)
        except Exception as exc:
            self._queue.put(("err", str(exc)))
        else:
            self._queue.put(("ok", reply))

    def refresh_models(self):
        """ดึงรายชื่อโมเดลจริงจาก API แล้วเติมใน drop-down"""
        if self._busy:
            return
        model = self._current_model()
        provider = ai.provider_for_model(model)
        key = self.key.text().strip() or ai.env_api_key(provider)
        if not key:
            self.key_hint.setText("ใส่ API key ของ %s ก่อนดึงรายการโมเดล"
                                  % ai.provider_label(provider))
            self.key.setFocus()
            return

        self._busy = True
        self.btn_send.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.status.setText("กำลังดึงรายการโมเดล…")
        threading.Thread(target=self._models_worker, args=(key, provider), daemon=True).start()
        self._timer.start()

    def _models_worker(self, key, provider):
        try:
            models = ai.list_models(key=key, provider=provider)
        except Exception as exc:
            self._queue.put(("models_err", str(exc)))
        else:
            self._queue.put(("models", models))

    def _apply_models(self, models):
        current = self.model.currentText().strip()
        self.model.blockSignals(True)
        self.model.clear()
        self.model.addItems(models)
        if current:
            self.model.setCurrentText(current)
        self.model.blockSignals(False)
        self._update_hint()
        if not models:
            return "ไม่พบโมเดลที่ใช้ได้กับคีย์นี้"
        return "พบ %d โมเดล — เลือกจากรายการได้เลย" % len(models)

    def _poll(self):
        try:
            kind, payload = self._queue.get_nowait()
        except queue.Empty:
            return
        self._timer.stop()
        note = ""
        if kind == "ok":
            self.messages.append({"role": "assistant", "content": payload})
            self._append("AI", payload, self._colors()["ai"])
        elif kind == "models":
            note = self._apply_models(payload)
        elif kind == "models_err":
            self._append(None, "ผิดพลาด: " + payload, self._colors()["err"])
        else:
            if self.messages and self.messages[-1].get("role") == "user":
                self.messages.pop()
            self._append(None, "ผิดพลาด: " + payload, self._colors()["err"])
        self._finish()
        if note:
            self.status.setText(note)

    def _finish(self):
        self._busy = False
        self.status.setText("")
        self.btn_send.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self.input.setFocus()

    def clear_chat(self):
        if self._busy:
            return
        if self.confirm_clear and len(self.messages) > 1:
            answer = QMessageBox.question(
                self, "ล้างบทสนทนา",
                "ต้องการล้างบทสนทนาทั้งหมดหรือไม่?\n(ข้อความจะหายและกู้คืนไม่ได้)",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
        self.messages = [{"role": "system", "content": ai.SYSTEM_PROMPT}]
        self.view.clear()
        self._append(None, self._hint_text(), self._colors()["muted"])
        self.status.setText("")

    def export_text(self):
        lines = []
        for message in self.messages[1:]:
            role = message.get("role")
            if role == "user":
                lines.append("คุณ: %s" % message.get("content", ""))
            elif role == "assistant":
                lines.append("AI: %s" % message.get("content", ""))
        return "\n\n".join(lines)


# ------------------------------------------------------------------- ตั้งค่า
class SettingsPage(BasePage):
    """หน้าตั้งค่า — ฟอนต์ ขนาดตัวอักษร ปุ่มลัด และพฤติกรรมของแอป"""

    def __init__(self, settings, on_change=None, on_save=None):
        super().__init__(
            "ตั้งค่า",
            "ปรับฟอนต์ ขนาดตัวอักษร ปุ่มลัด และพฤติกรรมของแอป — เก็บไว้ในเครื่องนี้เท่านั้น",
        )
        # เลื่อนได้ เพื่อให้ใช้งานได้ถึงขนาดตัวอักษร 150%
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        holder = QWidget()
        self.body = QVBoxLayout(holder)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(14)
        self.scroll.setWidget(holder)
        self.root.addWidget(self.scroll, 1)

        self.settings = appsettings.clean(settings)
        self.on_change = on_change
        self.on_save = on_save
        self._loading = False
        self._ui_touched = False
        self._mono_touched = False

        font_card = card("ฟอนต์")
        row = QHBoxLayout()
        row.addWidget(QLabel("ฟอนต์ UI"))
        self.ui_combo = QFontComboBox()
        self.ui_combo.setMinimumWidth(160)
        self.ui_combo.setMinimumHeight(34)
        row.addWidget(self.ui_combo, 1)
        row.addSpacing(14)
        row.addWidget(QLabel("ฟอนต์ mono"))
        self.mono_combo = QFontComboBox()
        self.mono_combo.setMinimumWidth(150)
        self.mono_combo.setMinimumHeight(34)
        row.addWidget(self.mono_combo, 1)
        font_card.body.addLayout(row)

        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("ขนาดตัวอักษร"))
        self.scale = QSlider(Qt.Horizontal)
        self.scale.setRange(80, 150)
        self.scale.setSingleStep(5)
        self.scale.setPageStep(10)
        self.scale.setMinimumWidth(220)
        scale_row.addWidget(self.scale, 1)
        self.scale_label = QLabel("100%")
        self.scale_label.setFixedWidth(52)
        scale_row.addWidget(self.scale_label)
        font_card.body.addLayout(scale_row)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("ธีม"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("มืด (Dark)", "dark")
        self.theme_combo.addItem("สว่าง (Light)", "light")
        self.theme_combo.setMinimumHeight(32)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch(1)
        font_card.body.addLayout(theme_row)

        font_hint = muted(
            "ฟอนต์ที่แนบมากับแอป: IBM Plex Sans Thai และ JetBrains Mono · "
            "ถ้าเครื่องไม่มีฟอนต์ที่เลือก แอปจะถอยไปใช้ฟอนต์สำรองให้อัตโนมัติ")
        font_hint.setWordWrap(True)
        font_card.body.addWidget(font_hint)
        self.body.addWidget(font_card)

        key_card = card("ปุ่มลัดและพฤติกรรม")
        send_row = QHBoxLayout()
        send_row.addWidget(QLabel("ปุ่มส่งข้อความในแชท AI"))
        self.send_combo = QComboBox()
        self.send_combo.addItem("Ctrl+Enter (Enter ขึ้นบรรทัดใหม่)", "ctrl+enter")
        self.send_combo.addItem("Enter (Shift+Enter ขึ้นบรรทัดใหม่)", "enter")
        self.send_combo.setMinimumHeight(32)
        send_row.addWidget(self.send_combo, 1)
        key_card.body.addLayout(send_row)

        self.cb_tabs = QCheckBox("สลับแท็บด้วย Ctrl+1 … Ctrl+6")
        self.cb_f5 = QCheckBox("F5 = สร้าง/เริ่มใหม่ในแท็บปัจจุบัน")
        self.cb_copy = QCheckBox("คัดลอกรหัสผ่านที่สร้างอัตโนมัติ")
        self.cb_clear = QCheckBox("ถามยืนยันก่อนล้างบทสนทนา AI")
        self.cb_model = QCheckBox("จำโมเดล AI ล่าสุดที่ใช้")
        for cb in (self.cb_tabs, self.cb_f5, self.cb_copy, self.cb_clear, self.cb_model):
            key_card.body.addWidget(cb)
        self.body.addWidget(key_card)

        actions = QHBoxLayout()
        self.btn_save = QPushButton("บันทึก")
        self.btn_save.setObjectName("Primary")
        self.btn_save.setMinimumHeight(36)
        self.btn_reset = QPushButton("คืนค่าเริ่มต้น")
        self.btn_reset.setObjectName("Ghost")
        self.btn_reset.setMinimumHeight(36)
        self.note = muted("")
        self.note.setWordWrap(True)
        actions.addWidget(self.btn_save)
        actions.addWidget(self.btn_reset)
        actions.addSpacing(10)
        actions.addWidget(self.note, 1)
        self.body.addLayout(actions)
        path_label = muted("ไฟล์ค่าตั้ง: %s" % appsettings.config_path())
        path_label.setWordWrap(True)
        self.body.addWidget(path_label)
        self.body.addStretch(1)

        self._load(self.settings)

        self.ui_combo.currentFontChanged.connect(lambda f: self._font_changed("ui"))
        self.mono_combo.currentFontChanged.connect(lambda f: self._font_changed("mono"))
        self.scale.valueChanged.connect(self._changed)
        self.theme_combo.currentIndexChanged.connect(self._changed)
        self.send_combo.currentIndexChanged.connect(self._changed)
        for cb in (self.cb_tabs, self.cb_f5, self.cb_copy, self.cb_clear, self.cb_model):
            cb.toggled.connect(self._changed)
        self.btn_save.clicked.connect(self.save)
        self.btn_reset.clicked.connect(self.reset)

    # ------------------------------------------------------------ ค่าในฟอร์ม
    def _load(self, values):
        self._loading = True
        try:
            self.ui_combo.setCurrentFont(QFont(values.get("ui_font") or appfonts.UI_FAMILY))
            self.mono_combo.setCurrentFont(QFont(values.get("mono_font") or appfonts.MONO_FAMILY))
            try:
                percent = int(round(float(values.get("font_scale", 1.0)) * 100))
            except (TypeError, ValueError):
                percent = 100
            self.scale.setValue(max(80, min(150, percent)))
            self.scale_label.setText("%d%%" % self.scale.value())
            theme_index = self.theme_combo.findData(values.get("theme", "dark"))
            self.theme_combo.setCurrentIndex(max(0, theme_index))
            index = self.send_combo.findData(values.get("send_key", "ctrl+enter"))
            self.send_combo.setCurrentIndex(max(0, index))
            self.cb_tabs.setChecked(bool(values.get("switch_tabs", True)))
            self.cb_f5.setChecked(bool(values.get("f5_generate", True)))
            self.cb_copy.setChecked(bool(values.get("auto_copy", False)))
            self.cb_clear.setChecked(bool(values.get("confirm_clear", True)))
            self.cb_model.setChecked(bool(values.get("remember_model", True)))
        finally:
            self._loading = False

    def values(self):
        ui_font = (self.ui_combo.currentFont().family().strip()
                   if self._ui_touched else self.settings.get("ui_font", ""))
        mono_font = (self.mono_combo.currentFont().family().strip()
                     if self._mono_touched else self.settings.get("mono_font", ""))
        return {
            "ui_font": ui_font,
            "mono_font": mono_font,
            "font_scale": round(self.scale.value() / 100.0, 2),
            "theme": self.theme_combo.currentData() or "dark",
            "send_key": self.send_combo.currentData() or "ctrl+enter",
            "switch_tabs": self.cb_tabs.isChecked(),
            "f5_generate": self.cb_f5.isChecked(),
            "auto_copy": self.cb_copy.isChecked(),
            "confirm_clear": self.cb_clear.isChecked(),
            "remember_model": self.cb_model.isChecked(),
            "last_model": self.settings.get("last_model", ""),
        }

    def set_theme(self, theme):
        """อัปเดต drop-down ธีมโดยไม่กระตุ้นการพรีวิวซ้ำ (เรียกจากเมนูมุมมอง)"""
        index = self.theme_combo.findData(theme)
        if index >= 0:
            blocked = self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(index)
            self.theme_combo.blockSignals(blocked)
        self.settings["theme"] = theme

    def set_scale(self, percent):
        """อัปเดตสไลเดอร์ขนาดตัวอักษรโดยไม่กระตุ้นการพรีวิวซ้ำ (เรียกจากเมนูซูม)"""
        percent = max(80, min(150, int(percent)))
        blocked = self.scale.blockSignals(True)
        self.scale.setValue(percent)
        self.scale.blockSignals(blocked)
        self.scale_label.setText("%d%%" % percent)
        self.settings["font_scale"] = round(percent / 100.0, 2)

    def _font_changed(self, which):
        if self._loading:
            return
        if which == "ui":
            self._ui_touched = True
        else:
            self._mono_touched = True
        self._changed()

    def _changed(self, *args):
        self.scale_label.setText("%d%%" % self.scale.value())
        if self._loading:
            return
        self.note.setText("ตัวอย่างมีผลทันที — กด “บันทึก” เพื่อเก็บถาวร")
        if self.on_change is not None:
            self.on_change(self.values())

    # -------------------------------------------------------------- ปุ่มจัดการ
    def save(self):
        values = self.values()
        ok = self.on_save(values) if self.on_save is not None else appsettings.save(values)
        self.settings = appsettings.clean(values)
        self._ui_touched = False
        self._mono_touched = False
        self.note.setText("บันทึกแล้ว ✓" if ok else "บันทึกไม่สำเร็จ — เขียนไฟล์ค่าตั้งไม่ได้")

    def reset(self):
        keep = {"last_model": self.settings.get("last_model", "")}
        self.settings = appsettings.clean(dict(appsettings.DEFAULTS, **keep))
        self._ui_touched = False
        self._mono_touched = False
        self._load(self.settings)
        self.note.setText("คืนค่าเริ่มต้นแล้ว — กด “บันทึก” เพื่อเก็บถาวร")
        if self.on_change is not None:
            self.on_change(self.values())


# ------------------------------------------------------------------ หน้าต่าง
class MainWindow(QMainWindow):
    def __init__(self, settings=None):
        super().__init__()
        self.settings = appsettings.clean(settings if settings is not None else appsettings.load())
        self._shortcuts = []
        self._shortcut_key = None
        self._find_text = ""
        self._last_dir = ""
        self.setWindowTitle("xpass — รหัสผ่าน / 2FA / ผู้ช่วย AI")
        self.resize(1060, 700)
        self.setMinimumSize(900, 620)

        root = QWidget()
        root.setObjectName("Root")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(222)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 22, 16, 18)
        side.setSpacing(6)

        brand = QLabel("xpass")
        brand.setObjectName("Brand")
        brand_sub = QLabel("ออฟไลน์ · ยกเว้นแท็บ AI")
        brand_sub.setObjectName("BrandSub")
        side.addWidget(brand)
        side.addWidget(brand_sub)
        side.addSpacing(18)

        self.stack = QStackedWidget()
        self.ai_page = AiPage(self.settings.get("last_model") or None)
        self.ai_page.on_model = self._remember_model
        self.settings_page = SettingsPage(self.settings, self.apply_settings, self._save_settings)
        self.pages = [PasswordPage(), NamePage(), AdminPage(), TotpPage(), self.ai_page,
                      self.settings_page]
        for page in self.pages:
            self.stack.addWidget(page)

        self.nav_names = ("รหัสผ่าน", "ชื่อหน้าลับ", "ชุดค่า admin", "TOTP สด", "ผู้ช่วย AI", "ตั้งค่า")
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for i, name in enumerate(self.nav_names):
            btn = QPushButton(name)
            btn.setObjectName("Nav")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            self.group.addButton(btn, i)
            side.addWidget(btn)
        self.group.button(0).setChecked(True)
        self.group.idClicked.connect(self._go)

        side.addStretch(1)
        foot = QLabel("โหมดหลักคำนวณในเครื่องนี้\nแท็บ “ผู้ช่วย AI” เท่านั้นที่เชื่อมต่ออินเทอร์เน็ต")
        foot.setObjectName("BrandSub")
        foot.setWordWrap(True)
        side.addWidget(foot)

        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.sidebar = sidebar

        self.toast = QLabel(self)
        self.toast.setObjectName("Toast")
        self.toast.setWordWrap(True)
        self.toast.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.toast.hide()
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self.toast.hide)

        self._build_menus()
        self.apply_settings()

    # ---------------------------------------------------------------- เมนู
    def _action(self, menu, text, slot, shortcut=None, checkable=False, checked=False,
                tip=None):
        """สร้าง QAction แล้วผูกกับเมนู (รองรับปุ่มลัดเดียวหรือหลายปุ่ม)"""
        action = QAction(text, self)
        if shortcut:
            if isinstance(shortcut, (list, tuple)):
                action.setShortcuts([QKeySequence(key) for key in shortcut])
            else:
                action.setShortcut(QKeySequence(shortcut))
        action.setCheckable(checkable)
        if checkable:
            action.setChecked(checked)
            action.toggled.connect(slot)
        else:
            action.triggered.connect(lambda _checked=False: slot())
        if tip:
            action.setStatusTip(tip)
        menu.addAction(action)
        return action

    def _build_menus(self):
        bar = self.menuBar()

        # 1) ไฟล์ — จัดการชิ้นงาน/ผลลัพธ์ของโปรแกรม
        file_menu = bar.addMenu("ไฟล์ (&File)")
        self._action(file_menu, "สร้างชุดใหม่ (New)", self._new_work, "Ctrl+N")
        file_menu.addSeparator()
        self._action(file_menu, "บันทึกผลลัพธ์… (Save As)", self._save_current, "Ctrl+S")
        self._action(file_menu, "ส่งออกทั้งหมด… (Export)", self._export_all, "Ctrl+Shift+S")
        self._action(file_menu, "นำเข้า secret TOTP… (Import)", self._import_secret, "Ctrl+O")
        file_menu.addSeparator()
        self._action(file_menu, "พิมพ์… (Print)", self._print_current, "Ctrl+P")
        file_menu.addSeparator()
        self._action(file_menu, "ปิดหน้าต่าง (Close)", self.close, "Ctrl+W")
        self._action(file_menu, "ออก (Exit)", self.close, "Ctrl+Q")

        # 2) แก้ไข — ทำงานกับช่องข้อความที่โฟกัสอยู่
        edit_menu = bar.addMenu("แก้ไข (&Edit)")
        self._action(edit_menu, "เลิกทำ (Undo)", self._edit_undo, "Ctrl+Z")
        self._action(edit_menu, "ทำซ้ำ (Redo)", self._edit_redo, ["Ctrl+Y", "Ctrl+Shift+Z"])
        edit_menu.addSeparator()
        self._action(edit_menu, "ตัด (Cut)", self._edit_cut, "Ctrl+X")
        self._action(edit_menu, "คัดลอก (Copy)", self._edit_copy, "Ctrl+C")
        self._action(edit_menu, "วาง (Paste)", self._edit_paste, "Ctrl+V")
        self._action(edit_menu, "เลือกทั้งหมด (Select All)", self._edit_select_all, "Ctrl+A")
        edit_menu.addSeparator()
        self._action(edit_menu, "ค้นหา… (Find)", self._find, "Ctrl+F")
        self._action(edit_menu, "แทนที่… (Replace)", self._replace, "Ctrl+H")

        # 3) มุมมอง — ปรับการแสดงผล ไม่กระทบข้อมูล
        view_menu = bar.addMenu("มุมมอง (&View)")
        self._action(view_menu, "ซูมเข้า (Zoom In)", lambda: self._zoom(5), ["Ctrl++", "Ctrl+="])
        self._action(view_menu, "ซูมออก (Zoom Out)", lambda: self._zoom(-5), "Ctrl+-")
        self._action(view_menu, "ขนาดปกติ (Reset Zoom)", self._zoom_reset, "Ctrl+0")
        view_menu.addSeparator()
        self.act_fullscreen = self._action(
            view_menu, "เต็มจอ (Full Screen)", self._toggle_fullscreen, "F11", checkable=True)
        self.act_sidebar = self._action(
            view_menu, "แถบด้านข้าง (Sidebar)", self._toggle_sidebar, "Ctrl+B",
            checkable=True, checked=True)
        view_menu.addSeparator()
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        self.theme_group = theme_group
        self.act_theme_dark = self._action(
            view_menu, "โหมดมืด (Dark Mode)",
            lambda checked: checked and self._set_theme("dark"), checkable=True)
        self.act_theme_light = self._action(
            view_menu, "โหมดสว่าง (Light Mode)",
            lambda checked: checked and self._set_theme("light"), checkable=True)
        theme_group.addAction(self.act_theme_dark)
        theme_group.addAction(self.act_theme_light)

        # 4) ตั้งค่า — ค่าของโปรแกรมและบัญชีผู้ใช้
        settings_menu = bar.addMenu("ตั้งค่า (&Settings)")
        self._action(settings_menu, "การตั้งค่า… (Preferences)", lambda: self._go(5), "Ctrl+,")
        self._action(settings_menu, "บันทึกค่าตั้ง (Save Settings)", self._save_settings_now)
        self._action(settings_menu, "บัญชีผู้ใช้… (Account)", self._show_account)
        settings_menu.addSeparator()
        self._action(settings_menu, "เปิดโฟลเดอร์ค่าตั้ง (Open Settings Folder)",
                     self._open_settings_folder)

        # 5) ช่วยเหลือ — คู่มือ อัปเดต และข้อมูลโปรแกรม
        help_menu = bar.addMenu("ช่วยเหลือ (&Help)")
        self._action(help_menu, "คู่มือการใช้งาน (User Guide)", self._show_help, "F1")
        self._action(help_menu, "ตรวจสอบการอัปเดต… (Check for Updates)", self._check_updates)
        help_menu.addSeparator()
        self._action(help_menu, "เกี่ยวกับ xpass (About)", self._show_about)

    def _sync_theme_actions(self):
        """ให้เครื่องหมายถูกในเมนูมุมมองตรงกับธีมปัจจุบัน"""
        theme = self.settings.get("theme", "dark")
        for action, value in ((getattr(self, "act_theme_dark", None), "dark"),
                              (getattr(self, "act_theme_light", None), "light")):
            if action is None:
                continue
            blocked = action.blockSignals(True)
            action.setChecked(theme == value)
            action.blockSignals(blocked)

    # ------------------------------------------------------------- ข้อความสั้น
    def _notify(self, text, timeout=4000):
        """แสดงข้อความชั่วคราวมุมขวาล่าง โดยไม่ดันเลย์เอาต์"""
        self.toast.setText(text)
        self._place_toast()
        self.toast.show()
        self.toast.raise_()
        if timeout:
            self._toast_timer.start(timeout)
        else:
            self._toast_timer.stop()

    def _place_toast(self):
        self.toast.setMaximumWidth(max(240, self.width() - 48))
        self.toast.ensurePolished()
        self.toast.adjustSize()
        margin = 24
        x = max(0, self.width() - self.toast.width() - margin)
        y = max(0, self.height() - self.toast.height() - margin)
        self.toast.move(x, y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "toast", None) is not None and self.toast.isVisible():
            self._place_toast()

    # ------------------------------------------------------- ไฟล์ / ผลลัพธ์
    def _page_text(self, page=None):
        page = page or self.stack.currentWidget()
        getter = getattr(page, "export_text", None)
        return (getter() if callable(getter) else "").strip()

    def _page_slug(self, page=None):
        page = page or self.stack.currentWidget()
        try:
            index = self.pages.index(page)
        except ValueError:
            index = 0
        return ("password", "secret-name", "admin", "totp", "ai", "settings")[index]

    def _dialog_dir(self):
        return self._last_dir or os.path.expanduser("~")

    def _remember_path(self, path):
        folder = os.path.dirname(path)
        if folder:
            self._last_dir = folder

    def _write_text(self, path, text):
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as exc:
            QMessageBox.critical(self, "บันทึกไม่สำเร็จ", "เขียนไฟล์ไม่ได้:\n%s" % exc)
            return False
        self._remember_path(path)
        self._notify("บันทึกแล้ว: %s" % path, 5000)
        return True

    def _save_current(self):
        text = self._page_text()
        if not text:
            QMessageBox.information(self, "บันทึกผลลัพธ์",
                                    "แท็บนี้ยังไม่มีผลลัพธ์ให้บันทึก — กดสร้างก่อนครับ")
            return
        name = "xpass-%s-%s.txt" % (time.strftime("%Y%m%d-%H%M%S"), self._page_slug())
        path, _ = QFileDialog.getSaveFileName(
            self, "บันทึกผลลัพธ์", os.path.join(self._dialog_dir(), name),
            "ไฟล์ข้อความ (*.txt);;Markdown (*.md);;ทุกไฟล์ (*)")
        if not path:
            return
        if not os.path.splitext(path)[1]:
            path += ".txt"
        self._write_text(path, text + "\n")

    def _export_all(self):
        parts = []
        for index, page in enumerate(self.pages):
            text = self._page_text(page)
            if text:
                parts.append("== %s ==\n%s" % (self.nav_names[index], text))
        if not parts:
            QMessageBox.information(self, "ส่งออกทั้งหมด",
                                    "ยังไม่มีผลลัพธ์ในแท็บใดเลย — กดสร้างก่อนครับ")
            return
        content = ("xpass — ส่งออกเมื่อ %s\n\n%s\n"
                   % (time.strftime("%Y-%m-%d %H:%M"), "\n\n".join(parts)))
        name = "xpass-export-%s.txt" % time.strftime("%Y%m%d-%H%M%S")
        path, _ = QFileDialog.getSaveFileName(
            self, "ส่งออกผลลัพธ์ทั้งหมด", os.path.join(self._dialog_dir(), name),
            "ไฟล์ข้อความ (*.txt);;Markdown (*.md);;ทุกไฟล์ (*)")
        if not path:
            return
        if not os.path.splitext(path)[1]:
            path += ".txt"
        self._write_text(path, content)

    def _import_secret(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "นำเข้า secret TOTP", self._dialog_dir(),
            "ไฟล์ข้อความ (*.txt *.ini *.md *.json *.url);;ทุกไฟล์ (*)")
        if not path:
            return
        try:
            if os.path.getsize(path) > 1024 * 1024:
                raise ValueError("ไฟล์ใหญ่เกิน 1 MB")
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                content = handle.read()
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "นำเข้าไม่สำเร็จ", str(exc))
            return

        match = re.search(r"secret[^A-Za-z2-7]{0,6}([A-Za-z2-7]{8,})", content, re.IGNORECASE)
        candidates = [match.group(1)] if match else re.findall(r"[A-Z2-7]{16,}", content.upper())
        if not candidates:
            QMessageBox.information(self, "นำเข้า secret TOTP",
                                    "ไม่พบ secret แบบ base32 ในไฟล์นี้")
            return

        secret = "".join(candidates[0].split()).upper()
        page = self.pages[3]
        if page.timer.isActive():
            page.toggle()  # หยุดก่อน เพื่อเริ่มใหม่ด้วย secret ที่นำเข้า
        page.secret.setText(secret)
        page.err.setText("")
        self._go(3)
        page.toggle()
        self._remember_path(path)
        self._notify("นำเข้า secret แล้ว — กำลังแสดงรหัส TOTP", 4000)

    def _print_current(self):
        text = self._page_text()
        if not text:
            QMessageBox.information(self, "พิมพ์",
                                    "แท็บนี้ยังไม่มีผลลัพธ์ให้พิมพ์ — กดสร้างก่อนครับ")
            return
        if QPrinter is None:
            QMessageBox.warning(self, "พิมพ์", "Qt PrintSupport ไม่พร้อมใช้งานในเครื่องนี้")
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("พิมพ์ผลลัพธ์ — %s" % self.nav_names[self.stack.currentIndex()])
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        document = QTextDocument()
        document.setPlainText(text)
        document.print_(printer)

    def _new_work(self):
        page = self.stack.currentWidget()
        if page is self.ai_page:
            self.ai_page.clear_chat()
        elif page is self.settings_page:
            self._go(0)
        elif isinstance(page, TotpPage):
            if page.timer.isActive():
                page.toggle()  # หยุดรหัสเดิม แล้วให้ใส่ secret ใหม่
            page.secret.setFocus()
        else:
            self._run_current()

    # ------------------------------------------------------------ แก้ไขข้อความ
    def _call_focus(self, *names):
        widget = QApplication.focusWidget()
        for name in names:
            handler = getattr(widget, name, None)
            if callable(handler):
                handler()
                return True
        return False

    def _edit_undo(self):
        self._call_focus("undo")

    def _edit_redo(self):
        self._call_focus("redo")

    def _edit_cut(self):
        if not self._call_focus("cut"):
            self._notify("เลือกข้อความในช่องที่แก้ไขได้ก่อนตัด", 3000)

    def _edit_copy(self):
        widget = QApplication.focusWidget()
        if isinstance(widget, (QLineEdit, QPlainTextEdit, QTextBrowser)):
            widget.copy()
            return
        text = self._page_text()
        if not text:
            self._notify("ไม่มีข้อความให้คัดลอก", 3000)
            return
        QGuiApplication.clipboard().setText(text)
        self._notify("คัดลอกผลลัพธ์ของแท็บนี้แล้ว", 3000)

    def _edit_paste(self):
        if not self._call_focus("paste"):
            self._notify("คลิกในช่องข้อความก่อนวาง", 3000)

    def _edit_select_all(self):
        if self._call_focus("selectAll"):
            return
        page = self.stack.currentWidget()
        for attr in ("text", "output", "view"):
            target = getattr(page, attr, None)
            if target is not None and callable(getattr(target, "selectAll", None)):
                target.setFocus()
                target.selectAll()
                return

    def _find(self):
        text, ok = QInputDialog.getText(self, "ค้นหา", "ค้นหาข้อความในแท็บนี้:",
                                        QLineEdit.Normal, self._find_text)
        if not ok or not text.strip():
            return
        self._find_text = text.strip()
        if self._find_in_page(self._find_text):
            self._notify("พบ “%s”" % self._find_text, 3000)
        else:
            QMessageBox.information(self, "ค้นหา",
                                    "ไม่พบ “%s” ในแท็บนี้" % self._find_text)

    def _find_in_page(self, needle):
        page = self.stack.currentWidget()
        widgets = []
        focus = QApplication.focusWidget()
        if isinstance(focus, (QTextBrowser, QPlainTextEdit, QLineEdit)):
            widgets.append(focus)
        for attr in ("view", "text", "output", "secret", "code"):
            widget = getattr(page, attr, None)
            if widget is not None and widget not in widgets:
                widgets.append(widget)
        if isinstance(page, AdminPage):
            widgets.extend(edit for edit in page.fields.values() if edit not in widgets)

        for widget in widgets:
            if isinstance(widget, (QTextBrowser, QPlainTextEdit)):
                if widget.find(needle):
                    widget.setFocus()
                    return True
            elif isinstance(widget, QLineEdit):
                index = widget.text().lower().find(needle.lower())
                if index >= 0:
                    widget.setFocus()
                    widget.setSelection(index, len(needle))
                    return True
            elif isinstance(widget, QLabel):
                if needle.lower() in widget.text().lower():
                    widget.setFocus()
                    return True
        return False

    def _replace(self):
        widget = QApplication.focusWidget()
        editable = (isinstance(widget, QLineEdit)
                    or (isinstance(widget, QPlainTextEdit) and not widget.isReadOnly()))
        if not editable:
            QMessageBox.information(
                self, "แทนที่",
                "คลิกในช่องข้อความที่แก้ไขได้ก่อน เช่น ช่อง secret TOTP หรือช่องพิมพ์แชท AI")
            return
        needle, ok = QInputDialog.getText(self, "แทนที่", "ค้นหาคำ:",
                                          QLineEdit.Normal, self._find_text)
        if not ok or not needle:
            return
        replacement, ok = QInputDialog.getText(self, "แทนที่", "แทนที่ด้วย:")
        if not ok:
            return

        if isinstance(widget, QLineEdit):
            content = widget.text()
            count = content.count(needle)
            if count:
                widget.setText(content.replace(needle, replacement))
        else:
            content = widget.toPlainText()
            count = content.count(needle)
            if count:
                widget.setPlainText(content.replace(needle, replacement))
        self._find_text = needle
        if count:
            self._notify("แทนที่แล้ว %d จุด" % count, 4000)
        else:
            QMessageBox.information(self, "แทนที่", "ไม่พบ “%s”" % needle)

    # ---------------------------------------------------------------- มุมมอง
    def _zoom(self, delta):
        percent = int(round(float(self.settings.get("font_scale", 1.0)) * 100))
        target = max(80, min(150, percent + delta))
        if target == percent:
            return
        self.settings["font_scale"] = round(target / 100.0, 2)
        self.settings_page.set_scale(target)
        self.apply_settings()
        self._notify(
            "ขนาดตัวอักษร %d%% — กด “บันทึก” ในหน้าตั้งค่าเพื่อเก็บถาวร" % target, 4000)

    def _zoom_reset(self):
        self.settings["font_scale"] = 1.0
        self.settings_page.set_scale(100)
        self.apply_settings()

    def _toggle_fullscreen(self, checked):
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()

    def _toggle_sidebar(self, checked):
        self.sidebar.setVisible(bool(checked))

    def _set_theme(self, theme):
        theme = "light" if theme == "light" else "dark"
        if theme == self.settings.get("theme", "dark"):
            return
        self.settings["theme"] = theme
        self.settings_page.set_theme(theme)
        self.apply_settings()
        ok = appsettings.save(self.settings)
        self._notify(
            "ธีม%s — %s" % ("สว่าง" if theme == "light" else "มืด",
                            "บันทึกค่าตั้งแล้ว" if ok else "เขียนไฟล์ค่าตั้งไม่ได้"), 3000)

    # -------------------------------------------------------- ตั้งค่า / ช่วยเหลือ
    def _save_settings_now(self):
        self._go(5)
        self.settings_page.save()

    def _show_account(self):
        QMessageBox.information(
            self, "บัญชีผู้ใช้",
            "xpass ไม่มีระบบบัญชีหรือคลาวด์ — ทุกอย่างคำนวณและเก็บไว้ในเครื่องนี้\n\n"
            "ค่าตั้ง (ฟอนต์ ขนาด ธีม และปุ่มลัด) เก็บที่:\n%s\n\n"
            "ไม่มีรหัสผ่าน TOTP secret หรือ API key ถูกบันทึกลงดิสก์"
            % appsettings.config_path())

    def _open_settings_folder(self):
        folder = appsettings.config_dir()
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            pass
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(folder)):
            QMessageBox.information(self, "โฟลเดอร์ค่าตั้ง", folder)

    def _show_help(self):
        readme = os.path.join(BASE, "README.md")
        box = QMessageBox(self)
        box.setWindowTitle("คู่มือการใช้งาน")
        box.setTextFormat(Qt.RichText)
        box.setText(
            "<h3>xpass %s</h3>"
            "<p>สร้างรหัสผ่าน รหัส 2FA (TOTP) และชื่อหน้าลับ — คำนวณในเครื่อง "
            "(ยกเว้นแท็บ “ผู้ช่วย AI”)</p>"
            "<ul>"
            "<li><b>รหัสผ่าน</b> — เลือกความยาว/จำนวน แล้วกดสร้าง</li>"
            "<li><b>ชื่อหน้าลับ</b> — สร้างชื่อไฟล์หรือ URL ที่คาดเดายาก</li>"
            "<li><b>ชุดค่า admin</b> — token, TOTP secret, ชื่อหน้า และ QR</li>"
            "<li><b>TOTP สด</b> — ใส่ secret base32 เพื่อดูรหัส 6 หลัก</li>"
            "<li><b>ผู้ช่วย AI</b> — ถามเรื่องความปลอดภัย (ต้องใช้ API key)</li>"
            "<li><b>ตั้งค่า</b> — ฟอนต์ ขนาด ธีม และปุ่มลัด</li>"
            "</ul>"
            "<p><b>ปุ่มลัด:</b> Ctrl+N สร้างใหม่ · Ctrl+S บันทึก · Ctrl+F ค้นหา · "
            "F5 สร้าง · F11 เต็มจอ · Ctrl+1…Ctrl+6 สลับแท็บ</p>"
            "<p>ไฟล์ค่าตั้ง: %s</p>" % (APP_VERSION, html.escape(appsettings.config_path())))
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        open_button = None
        if os.path.isfile(readme):
            open_button = box.addButton("เปิด README.md", QMessageBox.ButtonRole.ActionRole)
        box.exec()
        if open_button is not None and box.clickedButton() is open_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(readme))

    def _check_updates(self):
        QMessageBox.information(
            self, "ตรวจสอบการอัปเดต",
            "เวอร์ชันที่ใช้อยู่: %s\n\n"
            "xpass ไม่มีระบบอัปเดตอัตโนมัติและไม่เชื่อมต่อเซิร์ฟเวอร์เพื่อตรวจเวอร์ชัน "
            "เพื่อรักษาความเป็นส่วนตัว\n\n"
            "ถ้ามีไฟล์ติดตั้งรุ่นใหม่ ให้ติดตั้งทับได้เลย — ค่าตั้งเดิมจะยังอยู่"
            % APP_VERSION)

    def _show_about(self):
        QMessageBox.about(
            self, "เกี่ยวกับ xpass",
            "<h3>xpass %s</h3>"
            "<p>เครื่องมือสร้างรหัสผ่าน / รหัส 2FA (TOTP) / ชื่อหน้าลับ แบบออฟไลน์</p>"
            "<p>สัญญาอนุญาต MIT · © 2026 XRayTH</p>"
            "<p>ฟอนต์: IBM Plex Sans Thai และ JetBrains Mono (SIL OFL 1.1)<br>"
            "ผู้ช่วย AI (ออปชัน): OpenAI และ Google Gemini</p>"
            % APP_VERSION)

    # ------------------------------------------------------------ ใช้ค่าตั้ง
    def apply_settings(self, settings=None):
        """ใช้ค่าตั้งกับหน้าต่างทั้งหมดทันที (ฟอนต์ / ขนาด / ปุ่มลัด / พฤติกรรม)"""
        if settings is not None:
            self.settings = appsettings.clean(settings)
        current = self.settings

        ui_family, mono_family = appfonts.resolve_qt(current["ui_font"], current["mono_font"])
        app = QApplication.instance()
        if app is not None:
            appfonts.apply_qt_font(app, current["ui_font"], current["mono_font"],
                                   current["font_scale"])
        self.setStyleSheet(build_qss(ui_family, mono_family, current["font_scale"],
                                     current.get("theme", "dark")))
        self._sync_theme_actions()

        for page in self.pages:
            apply = getattr(page, "apply_settings", None)
            if callable(apply):
                apply(current)
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        current = self.settings
        key = (bool(current["switch_tabs"]), bool(current["f5_generate"]))
        if key != self._shortcut_key:
            self._shortcut_key = key
            for shortcut in self._shortcuts:
                shortcut.setEnabled(False)
                shortcut.deleteLater()
            self._shortcuts = []
            if key[0]:
                for i in range(len(self.pages)):
                    shortcut = QShortcut(QKeySequence("Ctrl+%d" % (i + 1)), self)
                    shortcut.activated.connect(lambda idx=i: self._go(idx))
                    self._shortcuts.append(shortcut)
            if key[1]:
                shortcut = QShortcut(QKeySequence("F5"), self)
                shortcut.activated.connect(self._run_current)
                self._shortcuts.append(shortcut)

        for i, name in enumerate(self.nav_names):
            btn = self.group.button(i)
            if btn is not None:
                btn.setToolTip(("Ctrl+%d — " % (i + 1) if current["switch_tabs"] else "") + name)

    def _go(self, index):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            btn = self.group.button(index)
            if btn is not None:
                btn.setChecked(True)

    def _run_current(self):
        page = self.stack.currentWidget()
        if page is self.ai_page:
            self.ai_page.input.setFocus()
            return
        generate = getattr(page, "generate", None)
        if callable(generate):
            generate()

    def _save_settings(self, values):
        data = dict(values)
        data["last_model"] = self.settings.get("last_model", "")
        self.settings = appsettings.clean(data)
        self.settings_page.settings = dict(self.settings)
        self.apply_settings()
        return appsettings.save(self.settings)

    def _remember_model(self, model):
        model = (model or "").strip()
        if not model or not self.settings.get("remember_model"):
            return
        if model == self.settings.get("last_model"):
            return
        self.settings["last_model"] = model
        self.settings_page.settings["last_model"] = model
        appsettings.save(self.settings)


def main():
    settings = appsettings.load()
    app = QApplication(sys.argv)
    app.setApplicationName("xpass")
    ui_family, mono_family = appfonts.setup_qt(
        app, settings["ui_font"], settings["mono_font"], settings["font_scale"])
    win = MainWindow(settings)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
