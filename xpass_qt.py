#!/usr/bin/env python3
"""xpass_qt: UI เวอร์ชัน PySide6 (Qt) — ธีมมืดทันสมัย

รัน:  python xpass_qt.py
ต้องมี: pip install PySide6   (และ qrcode ถ้าอยากเห็น QR)

ยังทำงานออฟไลน์ทั้งหมด ไม่เขียนไฟล์ ไม่เก็บค่าใด ๆ
ต้องวางไฟล์นี้ไว้โฟลเดอร์เดียวกับ xpass.py
"""
import math
import os
import secrets
import sys
import time

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPlainTextEdit, QProgressBar, QPushButton, QSizePolicy, QSlider,
    QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

try:
    import xpass as core
except Exception as exc:  # pragma: no cover
    raise SystemExit("ต้องวาง xpass_qt.py ไว้ในโฟลเดอร์เดียวกับ xpass.py (%s)" % exc)

QSS = """
QWidget { color: #e6e9ef; font-family: "Segoe UI", "Leelawadee UI", sans-serif; font-size: 13px; }
#Root { background: #0b0d10; }
#Sidebar { background: #0e1116; border-right: 1px solid #1a212c; }
#Brand { font-size: 23px; font-weight: 700; letter-spacing: 1px; }
#BrandSub { color: #79828f; font-size: 11px; }
#H1 { font-size: 20px; font-weight: 700; }
#H2 { font-size: 14px; font-weight: 600; }
#Muted { color: #79828f; font-size: 12px; }
#Err { color: #ff6b7d; font-size: 12px; }
#Ok { color: #3fcf7f; font-size: 12px; }
#Mono { font-family: "Cascadia Mono", "Consolas", monospace; font-size: 13px; }
#Big { font-family: "Cascadia Mono", "Consolas", monospace; font-size: 58px; font-weight: 700; }
#Badge { background: #1b2333; border-radius: 8px; padding: 3px 10px; font-weight: 600; color: #9fb6ff; }

QFrame#Card { background: #11151c; border: 1px solid #1d2430; border-radius: 14px; }

QPushButton { background: #1a212c; border: 1px solid #26303f; border-radius: 9px;
              padding: 8px 14px; color: #d6dbe6; }
QPushButton:hover { background: #232d3b; border-color: #334052; }
QPushButton:pressed { background: #1d2530; }

QPushButton#Nav { text-align: left; padding: 11px 14px; border: none; border-radius: 10px;
                  background: transparent; color: #98a1b0; font-size: 13px; }
QPushButton#Nav:hover { background: #161c26; color: #e6e9ef; }
QPushButton#Nav:checked { background: #1a2436; color: #ffffff; font-weight: 600; }

QPushButton#Primary { background: #4f7dff; border: none; color: #ffffff; font-weight: 600; }
QPushButton#Primary:hover { background: #6a92ff; }
QPushButton#Primary:pressed { background: #3f66d6; }

QPushButton#Ghost { background: transparent; border: 1px solid #26303f; }

QLineEdit, QPlainTextEdit, QSpinBox {
    background: #0d1117; border: 1px solid #222b38; border-radius: 9px;
    padding: 8px 10px; selection-background-color: #2f5bd0; color: #e6e9ef;
}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus { border: 1px solid #4f7dff; }
QLineEdit[readOnly="true"] { color: #b9c2d0; }
QPlainTextEdit { font-family: "Cascadia Mono", "Consolas", monospace; font-size: 14px; }

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
"""


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

    def generate(self):
        length, count = self.slider.value(), self.count.value()
        symbols, no_ambig = self.cb_sym.isChecked(), self.cb_amb.isChecked()
        lines, bits = [], 0.0
        for _ in range(count):
            p, bits = core.gen_password(length, symbols, no_ambig)
            lines.append(p)
        self.text.setPlainText("\n".join(lines))
        self.bits.setText("ประมาณ %d บิต entropy" % bits)


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


# ---------------------------------------------------------- ชุดค่า admin
class AdminPage(BasePage):
    def __init__(self):
        super().__init__("ชุดค่า admin", "สร้าง token, secret 2FA และชื่อหน้าลับสำหรับ Cloudflare Worker — แสดงครั้งเดียว ไม่บันทึกลงดิสก์")

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
        for key, label in (("token", "ADMIN_TOKEN"), ("secret", "ADMIN_TOTP_SECRET"),
                           ("page", "ชื่อหน้า admin ลับ"), ("uri", "ลิงก์ otpauth")):
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
        self.note.setStyleSheet("color: #3fcf7f; font-size: 12px;")
        self.note.setText("รหัสตอนนี้ควรตรงกับแอป: %s %s" % (code[:3], code[3:]))

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


# ------------------------------------------------------------------ หน้าต่าง
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("xpass — รหัสผ่าน / 2FA ออฟไลน์")
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
        brand_sub = QLabel("ออฟไลน์ · ไม่บันทึกข้อมูล")
        brand_sub.setObjectName("BrandSub")
        side.addWidget(brand)
        side.addWidget(brand_sub)
        side.addSpacing(18)

        self.stack = QStackedWidget()
        self.pages = [PasswordPage(), NamePage(), AdminPage(), TotpPage()]
        for p in self.pages:
            self.stack.addWidget(p)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for i, name in enumerate(("รหัสผ่าน", "ชื่อหน้าลับ", "ชุดค่า admin", "TOTP สด")):
            btn = QPushButton(name)
            btn.setObjectName("Nav")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            self.group.addButton(btn, i)
            side.addWidget(btn)
        self.group.button(0).setChecked(True)
        self.group.idClicked.connect(self.stack.setCurrentIndex)

        side.addStretch(1)
        foot = QLabel("ทุกอย่างคำนวณในเครื่องนี้\nไม่มีการเชื่อมต่ออินเทอร์เน็ต")
        foot.setObjectName("BrandSub")
        foot.setWordWrap(True)
        side.addWidget(foot)

        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        self.setStyleSheet(QSS)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("xpass")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
