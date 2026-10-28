#!/usr/bin/env python3
"""xpass_settings: ค่าตั้งของแอป xpass (ฟอนต์ / ขนาด / ธีม / ปุ่มลัด / พฤติกรรม)

- เก็บเป็น JSON ที่ %APPDATA%\\xpass\\settings.json (หรือ XPASS_CONFIG_DIR)
- เก็บเฉพาะค่าตั้ง ไม่เก็บรหัสผ่าน TOTP secret หรือ API key ใด ๆ
- ถ้าอ่าน/เขียนไม่ได้ จะใช้ค่าเริ่มต้นในหน่วยความจำแทน (แอปยังทำงานปกติ)
"""
from __future__ import annotations

import json
import os

APP_DIR_NAME = "xpass"
FILE_NAME = "settings.json"

DEFAULTS = {
    "ui_font": "",            # "" = ฟอนต์ที่แนบมากับแอป (IBM Plex Sans Thai)
    "mono_font": "",          # "" = JetBrains Mono
    "font_scale": 1.0,        # 0.8 – 1.5
    "theme": "dark",          # "dark" | "light"
    "send_key": "ctrl+enter",  # "ctrl+enter" | "enter"
    "switch_tabs": True,      # Ctrl+1 … Ctrl+6
    "f5_generate": True,      # F5 = สร้าง/เริ่มใหม่ในแท็บปัจจุบัน
    "auto_copy": False,       # คัดลอกรหัสผ่านที่สร้างอัตโนมัติ
    "confirm_clear": True,    # ถามก่อนล้างบทสนทนา AI
    "remember_model": True,   # จำโมเดล AI ล่าสุด
    "last_model": "",
}

_SEND_KEYS = ("ctrl+enter", "enter")
_THEMES = ("dark", "light")


def config_dir():
    """โฟลเดอร์เก็บค่าตั้ง (override ได้ด้วย XPASS_CONFIG_DIR)"""
    override = os.environ.get("XPASS_CONFIG_DIR", "").strip()
    if override:
        return override
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, APP_DIR_NAME)


def config_path():
    return os.path.join(config_dir(), FILE_NAME)


def clean(raw):
    """ตรวจและเติมค่าเริ่มต้นให้ค่าตั้งที่อาจไม่ครบ/ผิดรูปแบบ"""
    out = dict(DEFAULTS)
    if not isinstance(raw, dict):
        return out
    for key, default in DEFAULTS.items():
        value = raw.get(key, default)
        if isinstance(default, bool):
            out[key] = bool(value)
        elif isinstance(default, float):
            try:
                out[key] = max(0.8, min(1.5, round(float(value), 2)))
            except (TypeError, ValueError):
                out[key] = default
        else:
            out[key] = str(value or "").strip()[:120]
    if out["send_key"] not in _SEND_KEYS:
        out["send_key"] = DEFAULTS["send_key"]
    if out["theme"] not in _THEMES:
        out["theme"] = DEFAULTS["theme"]
    return out


def load():
    """อ่านค่าตั้งจากดิสก์ (ถ้าไม่มี/เสียหาย คืนค่าเริ่มต้น)"""
    try:
        with open(config_path(), "r", encoding="utf-8") as fh:
            return clean(json.load(fh))
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save(settings):
    """เขียนค่าตั้งลงดิสก์ — คืน True ถ้าสำเร็จ"""
    data = clean(settings)
    path = config_path()
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def reset():
    return dict(DEFAULTS)
