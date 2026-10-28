#!/usr/bin/env python3
"""xpass_fonts: ฟอนต์ไทย–อังกฤษชุดเดียวกับแอป

ใช้ฟอนต์ที่แนบมากับโปรแกรมก่อน (โฟลเดอร์ assets/fonts):
  - IBM Plex Sans Thai  → ข้อความ UI ไทย + อังกฤษ
  - JetBrains Mono      → รหัสผ่าน / TOTP / ค่าที่คัดลอก

ถ้าไม่พบไฟล์ฟอนต์ (เช่นรันจากที่อื่น) จะถอยไปใช้ฟอนต์ที่ติดตั้งใน Windows
โดยเลือกตัวที่สวยและรองรับภาษาไทยเป็นลำดับแรก

ลำดับความสำคัญของฟอนต์ที่เลือก:
  1) ค่าที่ผู้ใช้เลือกในหน้า “ตั้งค่า” ของแอป
  2) ตัวแปรสภาพแวดล้อม XPASS_FONT / XPASS_MONO_FONT
  3) ฟอนต์ที่แนบมากับแอป แล้วจึงฟอนต์สำรองของระบบ

ตัวแปรสภาพแวดล้อม:
  XPASS_FONT        ชื่อฟอนต์ UI     (เช่น "Sarabun")
  XPASS_MONO_FONT   ชื่อฟอนต์ mono   (เช่น "Consolas")
  XPASS_FONT_DIR    โฟลเดอร์ฟอนต์ที่ต้องการโหลดเพิ่ม
"""
from __future__ import annotations

import os
import sys

UI_FAMILY = "IBM Plex Sans Thai"
MONO_FAMILY = "JetBrains Mono"

# ลำดับฟอนต์สำรอง — ตัวแรกที่ติดตั้งอยู่ในเครื่องจะถูกใช้
UI_FALLBACKS = ("Segoe UI Variable Text", "Segoe UI", "Leelawadee UI", "Tahoma", "Arial")
MONO_FALLBACKS = ("Cascadia Mono", "Consolas", "Courier New")

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")


def font_dir():
    """โฟลเดอร์ฟอนต์ที่แนบมากับแอป (หรือที่ผู้ใช้กำหนดผ่าน XPASS_FONT_DIR)"""
    return os.environ.get("XPASS_FONT_DIR") or _FONT_DIR


def font_files():
    """รายชื่อไฟล์ฟอนต์ (.ttf/.otf) ที่จะโหลด — เรียงตามชื่อไฟล์"""
    folder = font_dir()
    if not os.path.isdir(folder):
        return []
    names = sorted(n for n in os.listdir(folder) if n.lower().endswith((".ttf", ".otf")))
    return [os.path.join(folder, n) for n in names]


def _pick(preferred, available):
    """คืนชื่อฟอนต์ตัวแรกที่มีอยู่จริง"""
    for name in preferred:
        if name and name in available:
            return name
    # ไม่พบเลย: ใช้ตัวสำรองทั่วไปตัวสุดท้าย เพื่อให้ยังมีชื่อฟอนต์ส่งต่อไป QSS/Tk
    return next((n for n in reversed(preferred) if n), "")


def _preferred(env_name, family, fallbacks, custom=""):
    first = (custom or "").strip() or os.environ.get(env_name, "").strip()
    return ([first] if first else []) + [family, *fallbacks]


def load_qt_fonts():
    """โหลดฟอนต์ที่แนบมาเข้า Qt — คืนจำนวนไฟล์ที่โหลดสำเร็จ"""
    try:
        from PySide6.QtGui import QFontDatabase
    except Exception:
        return 0
    loaded = 0
    for path in font_files():
        try:
            if QFontDatabase.addApplicationFont(path) >= 0:
                loaded += 1
        except Exception:
            pass
    return loaded


def load_tk_fonts():
    """โหลดฟอนต์แบบ private ให้ Tk/GDI เห็นโดยไม่ต้องติดตั้งลงระบบ"""
    if sys.platform != "win32":
        return 0
    try:
        import ctypes

        gdi32 = ctypes.windll.gdi32
        gdi32.AddFontResourceExW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
        gdi32.AddFontResourceExW.restype = ctypes.c_int
    except Exception:
        return 0
    loaded = 0
    for path in font_files():
        try:
            if gdi32.AddFontResourceExW(path, 0x10, None) > 0:  # FR_PRIVATE
                loaded += 1
        except Exception:
            pass
    return loaded


def resolve_qt(ui_pref="", mono_pref=""):
    """เลือกชื่อฟอนต์ Qt ที่มีอยู่จริง — คืน (ui, mono)"""
    try:
        from PySide6.QtGui import QFontDatabase
    except Exception:
        return UI_FAMILY, MONO_FAMILY
    available = set(QFontDatabase.families())
    return (
        _pick(_preferred("XPASS_FONT", UI_FAMILY, UI_FALLBACKS, ui_pref), available),
        _pick(_preferred("XPASS_MONO_FONT", MONO_FAMILY, MONO_FALLBACKS, mono_pref), available),
    )


def resolve_tk(root, ui_pref="", mono_pref=""):
    """เลือกชื่อฟอนต์ Tk ที่มีอยู่จริง — คืน (ui, mono)"""
    try:
        import tkinter.font as tkfont

        available = set(tkfont.families(root))
    except Exception:
        available = set()
    return (
        _pick(_preferred("XPASS_FONT", UI_FAMILY, UI_FALLBACKS, ui_pref), available),
        _pick(_preferred("XPASS_MONO_FONT", MONO_FAMILY, MONO_FALLBACKS, mono_pref), available),
    )


def apply_qt_font(app, ui_pref="", mono_pref="", scale=1.0):
    """ตั้งฟอนต์เริ่มต้นของ QApplication — คืน (ชื่อฟอนต์ UI, ชื่อฟอนต์ mono)"""
    try:
        from PySide6.QtGui import QFont
    except Exception:
        return UI_FAMILY, MONO_FAMILY

    ui, mono = resolve_qt(ui_pref, mono_pref)
    try:
        scale = max(0.8, min(1.5, float(scale)))
    except (TypeError, ValueError):
        scale = 1.0

    font = QFont()
    # ให้ Qt ถอยไปใช้ฟอนต์อื่นอัตโนมัติถ้าตัวหลักไม่มี glyph นั้น
    font.setFamilies([ui] + [f for f in UI_FALLBACKS if f])
    font.setPointSizeF(max(7.0, 10.0 * scale))
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    return ui, mono


def setup_qt(app, ui_pref="", mono_pref="", scale=1.0):
    """โหลดฟอนต์และตั้งฟอนต์เริ่มต้นของ QApplication

    คืน (ชื่อฟอนต์ UI, ชื่อฟอนต์ mono) สำหรับใช้ใน QSS
    """
    load_qt_fonts()
    return apply_qt_font(app, ui_pref, mono_pref, scale)


def configure_tk_fonts(root, ui):
    """ตั้ง named font ของ Tk ให้ทั้งแอปใช้ฟอนต์เดียวกัน (ขนาดเป็น point)"""
    try:
        import tkinter.font as tkfont
    except Exception:
        return
    for name, size, weight in (
        ("TkDefaultFont", 10, "normal"),
        ("TkTextFont", 10, "normal"),
        ("TkMenuFont", 10, "normal"),
        ("TkHeadingFont", 10, "bold"),
        ("TkCaptionFont", 9, "normal"),
        ("TkSmallCaptionFont", 9, "normal"),
        ("TkIconFont", 10, "normal"),
        ("TkTooltipFont", 9, "normal"),
    ):
        try:
            tkfont.nametofont(name).configure(family=ui, size=size, weight=weight)
        except Exception:
            pass


def setup_tk(root, ui_pref="", mono_pref="", scale=1.0):
    """โหลดฟอนต์และตั้ง named font ของ Tk ให้ทั้งแอปใช้ฟอนต์เดียวกัน

    scale: ตัวคูณขนาดตัวอักษร (0.8–1.5) ผ่าน tk scaling
    คืน (ชื่อฟอนต์ UI, ชื่อฟอนต์ mono)
    """
    load_tk_fonts()
    ui, mono = resolve_tk(root, ui_pref, mono_pref)
    try:
        scale = max(0.8, min(1.5, float(scale)))
    except (TypeError, ValueError):
        scale = 1.0
    if abs(scale - 1.0) > 0.001:
        try:
            base = float(root.tk.call("tk", "scaling"))
            root.tk.call("tk", "scaling", base * scale)
        except Exception:
            pass
    configure_tk_fonts(root, ui)
    return ui, mono
