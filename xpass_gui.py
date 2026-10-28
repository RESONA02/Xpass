#!/usr/bin/env python3
"""xpass_gui: หน้าต่าง GUI ของ xpass (tkinter, ใช้ stdlib ล้วน)

รัน:  python xpass_gui.py
หรือ: pythonw xpass_gui.py   (เปิดแบบไม่มีหน้าต่างดำ)

ทำงานออฟไลน์ (ยกเว้นแท็บ “ผู้ช่วย AI”) — เขียนเฉพาะไฟล์ค่าตั้งของผู้ใช้
(ฟอนต์/ขนาด/ปุ่มลัด) ไม่เก็บข้อมูลลับและไม่ส่งข้อมูลออกไปไหน
ต้องวางไฟล์นี้ไว้โฟลเดอร์เดียวกับ xpass.py
"""
import math
import os
import queue
import secrets
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

try:
    import xpass as core
except Exception as exc:  # pragma: no cover
    raise SystemExit("ต้องวาง xpass_gui.py ไว้ในโฟลเดอร์เดียวกับ xpass.py (%s)" % exc)

import xpass_fonts as appfonts
import xpass_ai as ai
import xpass_settings as appsettings

# ให้ตัวอักษรคมบนจอความละเอียดสูง (Windows)
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

FG_MUTED = "#5f6368"
FG_OK = "#1b7f3b"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings = appsettings.load()
        self.title("xpass — รหัสผ่าน / 2FA / ผู้ช่วย AI")
        self.geometry("820x640")
        self.minsize(720, 580)

        style = ttk.Style(self)
        for name in ("vista", "clam", "default"):
            if name in style.theme_names():
                style.theme_use(name)
                break

        # ฟอนต์ไทย–อังกฤษ (IBM Plex Sans Thai + JetBrains Mono)
        # เก็บ tk scaling เดิมไว้ เพื่อปรับขนาดตามค่าตั้งได้ตลอดการใช้งาน
        try:
            self._base_scaling = float(self.tk.call("tk", "scaling"))
        except Exception:
            self._base_scaling = 1.0
        ui, mono = appfonts.setup_tk(self, self.settings["ui_font"], self.settings["mono_font"],
                                     self.settings["font_scale"])
        self.ui_font = (ui, 10)
        self.mono_font = (mono, 10)
        self.mono_big_font = (mono, 44, "bold")
        self.heading_font = (ui, 20, "bold")
        self._configure_styles(ui, mono)

        self._totp_job = None
        self._totp_key = None
        self._totp_code = ""

        self._ai_messages = [{"role": "system", "content": ai.SYSTEM_PROMPT}]
        self._ai_queue = queue.Queue()
        self._ai_busy = False

        self._build()
        self.apply_settings()

    # -------------------------------------------------------------- ค่าตั้ง/ธีม
    def _configure_styles(self, ui, mono):
        style = ttk.Style(self)
        style.configure(".", font=(ui, 10))
        style.configure("TLabel", font=(ui, 10))
        style.configure("TButton", font=(ui, 10), padding=(12, 6))
        style.configure("TEntry", font=(ui, 10))
        style.configure("TSpinbox", font=(ui, 10))
        style.configure("TCheckbutton", font=(ui, 10))
        style.configure("TCombobox", font=(ui, 10))
        style.configure("TNotebook.Tab", font=(ui, 10), padding=(14, 7))
        style.configure("Title.TLabel", font=(ui, 20, "bold"))
        style.configure("Sub.TLabel", font=(ui, 9), foreground=FG_MUTED)
        style.configure("Ok.TLabel", font=(ui, 9), foreground=FG_OK)
        style.configure("Big.TLabel", font=(mono, 44, "bold"))
        style.configure("Mono.TEntry", font=(mono, 10))

    def _retag_widget(self, widget, old_ui, old_mono, ui, mono):
        """เปลี่ยนชื่อฟอนต์ของวิดเจ็ตที่ระบุฟอนต์ไว้ตรง ๆ (Text/Entry ฯลฯ)"""
        try:
            spec = widget.cget("font")
        except (tk.TclError, AttributeError):
            spec = ""
        if spec:
            try:
                parts = self.tk.splitlist(spec)
            except tk.TclError:
                parts = []
            if parts:
                family = parts[0]
                if family == old_mono:
                    new = mono
                elif family == old_ui:
                    new = ui
                else:
                    new = None
                if new and new != family:
                    try:
                        widget.configure(font=(new, *parts[1:]))
                    except tk.TclError:
                        pass
        for child in widget.winfo_children():
            self._retag_widget(child, old_ui, old_mono, ui, mono)

    def _apply_fonts(self):
        current = self.settings
        old_ui, old_mono = self.ui_font[0], self.mono_font[0]
        try:
            self.tk.call("tk", "scaling", self._base_scaling * current["font_scale"])
        except Exception:
            pass
        ui, mono = appfonts.resolve_tk(self, current["ui_font"], current["mono_font"])
        appfonts.configure_tk_fonts(self, ui)
        self.ui_font = (ui, 10)
        self.mono_font = (mono, 10)
        self.mono_big_font = (mono, 44, "bold")
        self.heading_font = (ui, 20, "bold")
        self._configure_styles(ui, mono)
        self._retag_widget(self, old_ui, old_mono, ui, mono)

    def _bind_shortcuts(self):
        total = len(self.nb.tabs())
        for i in range(total):
            sequence = "<Control-Key-%d>" % (i + 1)
            self.unbind_all(sequence)
            if self.settings.get("switch_tabs"):
                self.bind_all(sequence, lambda event, idx=i: self._go_tab(idx))
        self.unbind_all("<F5>")
        if self.settings.get("f5_generate"):
            self.bind_all("<F5>", lambda event: self._run_current())

    def _bind_ai_send(self):
        if not hasattr(self, "ai_input"):
            return
        for sequence in ("<Control-Return>", "<Return>", "<Shift-Return>"):
            self.ai_input.unbind(sequence)
        if self.settings.get("send_key") == "enter":
            self.ai_input.bind("<Return>", lambda event: (self._ai_send(), "break")[1])
            self.ai_input.bind("<Shift-Return>", lambda event: None)
        else:
            self.ai_input.bind("<Control-Return>", lambda event: (self._ai_send(), "break")[1])
        if hasattr(self, "ai_foot_hint"):
            self.ai_foot_hint.config(
                text="ส่งด้วย Enter" if self.settings.get("send_key") == "enter"
                else "ส่งด้วย Ctrl+Enter")

    def _go_tab(self, index):
        try:
            self.nb.select(index)
        except tk.TclError:
            return
        self.status("แท็บ: %s" % self.nb.tab(index, "text").strip())

    def _run_current(self):
        current = self.nb.index(self.nb.select())
        if current == 0:
            self.do_pw()
        elif current == 1:
            self.do_name()
        elif current == 2:
            self.do_admin()
        elif current == 4:
            self.ai_input.focus_set()
        return "break"

    def apply_settings(self, values=None):
        """ใช้ค่าตั้งทันที (ฟอนต์ / ขนาด / ปุ่มลัด / พฤติกรรม)"""
        if values is not None:
            data = dict(values)
            if not data.get("last_model"):
                data["last_model"] = self.settings.get("last_model", "")
            self.settings = appsettings.clean(data)
        self._apply_fonts()
        self._bind_shortcuts()
        self._bind_ai_send()

    # ------------------------------------------------------ หน้าตั้งค่า (แท็บ 6)
    def tab_settings(self, f):
        self._loading_settings = False
        families = sorted(set(tkfont.families(self)))

        font_box = ttk.Frame(f, padding=(18, 14, 18, 4))
        font_box.pack(fill="x")
        ttk.Label(font_box, text="ฟอนต์ UI").grid(row=0, column=0, sticky="w", pady=4)
        self.st_ui = tk.StringVar(value=self.settings["ui_font"] or self.ui_font[0])
        self.st_ui_box = ttk.Combobox(font_box, textvariable=self.st_ui, values=families,
                                      state="readonly", width=32)
        self.st_ui_box.grid(row=0, column=1, sticky="we", padx=8, pady=4)

        ttk.Label(font_box, text="ฟอนต์ mono").grid(row=0, column=2, sticky="w",
                                                    padx=(14, 0), pady=4)
        self.st_mono = tk.StringVar(value=self.settings["mono_font"] or self.mono_font[0])
        self.st_mono_box = ttk.Combobox(font_box, textvariable=self.st_mono, values=families,
                                        state="readonly", width=28)
        self.st_mono_box.grid(row=0, column=3, sticky="we", padx=8, pady=4)
        font_box.columnconfigure(1, weight=1)
        font_box.columnconfigure(3, weight=1)

        ttk.Label(font_box, text="ขนาดตัวอักษร").grid(row=1, column=0, sticky="w", pady=4)
        self.st_scale = tk.IntVar(value=int(round(self.settings["font_scale"] * 100)))
        scale = ttk.Scale(font_box, from_=80, to=150, orient="horizontal", variable=self.st_scale,
                          command=self._on_scale)
        scale.grid(row=1, column=1, sticky="we", padx=8, pady=4)
        self.st_scale_label = ttk.Label(font_box, text="%d%%" % self.st_scale.get(), width=6,
                                        style="Sub.TLabel")
        self.st_scale_label.grid(row=1, column=2, sticky="w", padx=(14, 0))
        ttk.Label(font_box, text="80–150% (มีผลทันที)", style="Sub.TLabel").grid(
            row=1, column=3, sticky="w", padx=8)

        key_box = ttk.Frame(f, padding=(18, 8, 18, 4))
        key_box.pack(fill="x")
        ttk.Label(key_box, text="ปุ่มส่งข้อความในแชท AI").grid(row=0, column=0, sticky="w", pady=4)
        self.st_send = tk.StringVar(value=("Enter (Shift+Enter ขึ้นบรรทัดใหม่)"
                                           if self.settings["send_key"] == "enter"
                                           else "Ctrl+Enter (Enter ขึ้นบรรทัดใหม่)"))
        send_box = ttk.Combobox(key_box, textvariable=self.st_send, state="readonly", width=38,
                                values=("Ctrl+Enter (Enter ขึ้นบรรทัดใหม่)",
                                        "Enter (Shift+Enter ขึ้นบรรทัดใหม่)"))
        send_box.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        self.st_tabs = tk.BooleanVar(value=self.settings["switch_tabs"])
        self.st_f5 = tk.BooleanVar(value=self.settings["f5_generate"])
        self.st_copy = tk.BooleanVar(value=self.settings["auto_copy"])
        self.st_clear = tk.BooleanVar(value=self.settings["confirm_clear"])
        self.st_model = tk.BooleanVar(value=self.settings["remember_model"])
        checks = (
            ("สลับแท็บด้วย Ctrl+1 … Ctrl+6", self.st_tabs),
            ("F5 = สร้าง/เริ่มใหม่ในแท็บปัจจุบัน", self.st_f5),
            ("คัดลอกรหัสผ่านที่สร้างอัตโนมัติ", self.st_copy),
            ("ถามยืนยันก่อนล้างบทสนทนา AI", self.st_clear),
            ("จำโมเดล AI ล่าสุดที่ใช้", self.st_model),
        )
        check_box = ttk.Frame(f, padding=(18, 6, 18, 4))
        check_box.pack(fill="x")
        for i, (text, var) in enumerate(checks):
            ttk.Checkbutton(check_box, text=text, variable=var,
                            command=self._settings_changed).grid(row=i, column=0, sticky="w",
                                                                 pady=2)

        actions = ttk.Frame(f, padding=(18, 10, 18, 4))
        actions.pack(fill="x")
        ttk.Button(actions, text="บันทึก", command=self.save_settings).pack(side="left")
        ttk.Button(actions, text="คืนค่าเริ่มต้น", command=self.reset_settings).pack(
            side="left", padx=8)
        self.st_note = ttk.Label(actions, text="", style="Sub.TLabel", wraplength=520)
        self.st_note.pack(side="left", padx=10)

        ttk.Label(f, text="ไฟล์ค่าตั้ง: %s" % appsettings.config_path(),
                  style="Sub.TLabel", padding=(18, 4, 18, 10), wraplength=760).pack(fill="x")

        for var in (self.st_ui, self.st_mono, self.st_send):
            var.trace_add("write", lambda *a: self._settings_changed())

    def _on_scale(self, value):
        try:
            self.st_scale.set(int(float(value)))
        except (TypeError, ValueError):
            return
        if not hasattr(self, "st_scale_label"):
            return
        self.st_scale_label.config(text="%d%%" % self.st_scale.get())
        self._settings_changed()

    def _settings_values(self):
        return {
            "ui_font": self.st_ui.get().strip(),
            "mono_font": self.st_mono.get().strip(),
            "font_scale": round(self.st_scale.get() / 100.0, 2),
            "theme": self.settings.get("theme", "dark"),
            "send_key": "enter" if self.st_send.get().startswith("Enter") else "ctrl+enter",
            "switch_tabs": bool(self.st_tabs.get()),
            "f5_generate": bool(self.st_f5.get()),
            "auto_copy": bool(self.st_copy.get()),
            "confirm_clear": bool(self.st_clear.get()),
            "remember_model": bool(self.st_model.get()),
            "last_model": self.settings.get("last_model", ""),
        }

    def _settings_changed(self):
        if getattr(self, "_loading_settings", False) or not hasattr(self, "st_note"):
            return
        self.st_note.config(text="ตัวอย่างมีผลทันที — กด “บันทึก” เพื่อเก็บถาวร")
        self.apply_settings(self._settings_values())

    def _load_settings(self, values):
        self._loading_settings = True
        try:
            self.st_ui.set(values.get("ui_font") or appfonts.UI_FAMILY)
            self.st_mono.set(values.get("mono_font") or appfonts.MONO_FAMILY)
            self.st_scale.set(int(round(float(values.get("font_scale", 1.0)) * 100)))
            self.st_scale_label.config(text="%d%%" % self.st_scale.get())
            self.st_send.set("Enter (Shift+Enter ขึ้นบรรทัดใหม่)"
                             if values.get("send_key") == "enter"
                             else "Ctrl+Enter (Enter ขึ้นบรรทัดใหม่)")
            self.st_tabs.set(bool(values.get("switch_tabs", True)))
            self.st_f5.set(bool(values.get("f5_generate", True)))
            self.st_copy.set(bool(values.get("auto_copy", False)))
            self.st_clear.set(bool(values.get("confirm_clear", True)))
            self.st_model.set(bool(values.get("remember_model", True)))
        finally:
            self._loading_settings = False

    def save_settings(self):
        values = self._settings_values()
        self.apply_settings(values)
        ok = appsettings.save(self.settings)
        self.st_note.config(text="บันทึกแล้ว ✓" if ok else "บันทึกไม่สำเร็จ — เขียนไฟล์ค่าตั้งไม่ได้")
        self.status("บันทึกค่าตั้งแล้ว" if ok else "บันทึกค่าตั้งไม่สำเร็จ")

    def reset_settings(self):
        data = dict(appsettings.DEFAULTS, last_model=self.settings.get("last_model", ""))
        self._load_settings(data)
        self.apply_settings(data)
        self.st_note.config(text="คืนค่าเริ่มต้นแล้ว — กด “บันทึก” เพื่อเก็บถาวร")

    # ------------------------------------------------------------------ โครง
    def _build(self):
        self.statusbar = ttk.Label(self, text="พร้อมใช้งาน", padding=(14, 6), foreground=FG_MUTED)
        self.statusbar.pack(side="bottom", fill="x")

        head = ttk.Frame(self, padding=(18, 14, 18, 0))
        head.pack(fill="x")
        ttk.Label(head, text="xpass", style="Title.TLabel").pack(side="left")
        ttk.Label(head, text="รหัสผ่าน · 2FA · ชื่อลับ", style="Sub.TLabel").pack(
            side="left", padx=(10, 0), pady=(9, 0))
        ttk.Label(head, text="● ออฟไลน์ (ยกเว้นแท็บ AI)", style="Ok.TLabel").pack(side="right", pady=(9, 0))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=14, pady=12)
        self.nb = nb
        for name, builder in (
            ("รหัสผ่าน", self.tab_password),
            ("ชื่อหน้าลับ", self.tab_name),
            ("ชุดค่า admin", self.tab_admin),
            ("TOTP สด", self.tab_totp),
            ("ผู้ช่วย AI", self.tab_ai),
            ("ตั้งค่า", self.tab_settings),
        ):
            frame = ttk.Frame(nb)
            nb.add(frame, text="   %s   " % name)
            builder(frame)

    def status(self, text):
        self.statusbar.config(text=text)

    def copy(self, text, btn=None):
        if not text:
            self.status("ไม่มีข้อมูลให้คัดลอก")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()  # บังคับให้ Tk เขียนลงคลิปบอร์ดของ Windows ทันที
        self.status("คัดลอกแล้ว ✓")
        if btn is not None:
            old = btn.cget("text")
            btn.config(text="คัดลอกแล้ว ✓")
            self.after(1200, lambda: btn.config(text=old))

    # ------------------------------------------------------ แท็บ 1: รหัสผ่าน
    def tab_password(self, f):
        box = ttk.Frame(f, padding=(18, 16, 18, 10))
        box.pack(fill="x")

        ttk.Label(box, text="ความยาว").grid(row=0, column=0, sticky="w")
        self.pw_len = tk.IntVar(value=20)
        scale = ttk.Scale(box, from_=8, to=64, orient="horizontal", variable=self.pw_len,
                          command=lambda v: (self.pw_len.set(int(float(v))),
                                             self.pw_len_lbl.config(text=int(float(v)))))
        scale.grid(row=0, column=1, sticky="we", padx=10, pady=4)
        self.pw_len_lbl = ttk.Label(box, text="20", width=4)
        self.pw_len_lbl.grid(row=0, column=2)

        self.pw_sym = tk.BooleanVar(value=True)
        self.pw_amb = tk.BooleanVar(value=False)
        ttk.Checkbutton(box, text="ใส่สัญลักษณ์ !@#$…", variable=self.pw_sym).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Checkbutton(box, text="ตัดตัวที่อ่านสับสน Il1O0o", variable=self.pw_amb).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Label(box, text="จำนวน").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.pw_count = tk.IntVar(value=1)
        ttk.Spinbox(box, from_=1, to=20, width=5, textvariable=self.pw_count).grid(
            row=3, column=1, sticky="w", padx=10, pady=(8, 0))

        box.columnconfigure(1, weight=1)

        out = ttk.Frame(f, padding=(18, 0, 18, 14))
        out.pack(fill="both", expand=True)
        self.pw_out = tk.Text(out, height=8, font=self.mono_font, wrap="none",
                              relief="solid", borderwidth=1, padx=10, pady=8, spacing3=3)
        self.pw_out.pack(fill="both", expand=True)

        row = ttk.Frame(out)
        row.pack(fill="x", pady=(10, 0))
        ttk.Button(row, text="สร้างรหัสผ่าน", command=self.do_pw).pack(side="left")
        ttk.Button(row, text="คัดลอกทั้งหมด",
                   command=lambda: self.copy(self.pw_out.get("1.0", "end").strip())).pack(side="left", padx=6)
        ttk.Button(row, text="ล้าง", command=lambda: self.pw_out.delete("1.0", "end")).pack(side="left")
        self.pw_bits = ttk.Label(row, text="", style="Sub.TLabel")
        self.pw_bits.pack(side="right")

    def do_pw(self):
        try:
            length = int(self.pw_len.get())
            count = max(1, min(int(self.pw_count.get()), 20))
        except Exception:
            return self.status("ค่าที่ใส่ไม่ถูกต้อง")
        if not 8 <= length <= 128:
            return messagebox.showerror("ผิดพลาด", "ความยาวต้องอยู่ระหว่าง 8–128")
        symbols, no_ambig = self.pw_sym.get(), self.pw_amb.get()
        lines, bits = [], 0.0
        for _ in range(count):
            p, bits = core.gen_password(length, symbols, no_ambig)
            lines.append(p)
        self.pw_out.delete("1.0", "end")
        self.pw_out.insert("1.0", "\n".join(lines))
        self.pw_bits.config(text="ประมาณ %d บิต entropy" % bits)
        self.status("สร้างรหัสผ่าน %d ชุด" % count)
        if self.settings.get("auto_copy"):
            self.copy("\n".join(lines))

    # ---------------------------------------------------- แท็บ 2: ชื่อหน้าลับ
    def tab_name(self, f):
        box = ttk.Frame(f, padding=(18, 16, 18, 10))
        box.pack(fill="x")

        ttk.Label(box, text="ความยาว (8–64)").grid(row=0, column=0, sticky="w")
        self.nm_len = tk.IntVar(value=24)
        ttk.Spinbox(box, from_=8, to=64, width=6, textvariable=self.nm_len).grid(
            row=0, column=1, sticky="w", padx=10, pady=4)

        ttk.Label(box, text="คำนำหน้า").grid(row=1, column=0, sticky="w")
        self.nm_prefix = tk.StringVar(value="a-")
        ttk.Entry(box, textvariable=self.nm_prefix, width=12).grid(
            row=1, column=1, sticky="w", padx=10, pady=4)

        ttk.Button(box, text="สร้างชื่อ", command=self.do_name).grid(
            row=2, column=0, sticky="w", pady=(10, 0))

        out = ttk.Frame(f, padding=(18, 12, 18, 14))
        out.pack(fill="x")
        ttk.Label(out, text="ชื่อไฟล์ / URL", style="Sub.TLabel").pack(anchor="w")
        line = ttk.Frame(out)
        line.pack(fill="x", pady=(4, 0))
        self.nm_out = tk.StringVar(value="")
        entry = ttk.Entry(line, textvariable=self.nm_out, font=self.mono_font, state="readonly")
        entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.nm_btn = ttk.Button(line, text="คัดลอก",
                                 command=lambda: self.copy(self.nm_out.get(), self.nm_btn))
        self.nm_btn.pack(side="left", padx=(8, 0))
        self.nm_bits = ttk.Label(out, text="", style="Sub.TLabel")
        self.nm_bits.pack(anchor="w", pady=(8, 0))

    def do_name(self):
        try:
            n = max(8, min(int(self.nm_len.get()), 64))
        except Exception:
            return self.status("ความยาวไม่ถูกต้อง")
        page = "%s%s.html" % (self.nm_prefix.get().strip(), core.gen_slug(n))
        self.nm_out.set(page)
        self.nm_bits.config(text="ประมาณ %d บิต entropy" % (n * math.log2(36)))
        self.status("สร้างชื่อหน้าลับแล้ว")

    # ---------------------------------------------------- แท็บ 3: admin + QR
    def tab_admin(self, f):
        wrap = ttk.Frame(f, padding=(18, 14, 18, 14))
        wrap.pack(fill="both", expand=True)
        left = ttk.Frame(wrap)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(wrap)
        right.pack(side="right", fill="y", padx=(16, 0))

        form = ttk.Frame(left)
        form.pack(fill="x")
        ttk.Label(form, text="Issuer").grid(row=0, column=0, sticky="w")
        self.ad_issuer = tk.StringVar(value="XRay Admin")
        ttk.Entry(form, textvariable=self.ad_issuer, width=22).grid(
            row=0, column=1, sticky="w", padx=8, pady=3)
        ttk.Label(form, text="บัญชี").grid(row=1, column=0, sticky="w")
        self.ad_account = tk.StringVar(value="admin")
        ttk.Entry(form, textvariable=self.ad_account, width=22).grid(
            row=1, column=1, sticky="w", padx=8, pady=3)
        ttk.Button(form, text="สร้างชุดค่า admin", command=self.do_admin).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

        self.ad_values = {}
        vals = ttk.Frame(left)
        vals.pack(fill="x", pady=(14, 0))
        for i, (key, label) in enumerate((
            ("token", "ADMIN_TOKEN"),
            ("secret", "ADMIN_TOTP_SECRET"),
            ("page", "ชื่อหน้า admin"),
            ("uri", "ลิงก์ otpauth"),
        )):
            ttk.Label(vals, text=label, style="Sub.TLabel").grid(row=i * 2, column=0, columnspan=3, sticky="w",
                                                                 pady=(8 if i else 0, 2))
            var = tk.StringVar()
            entry = ttk.Entry(vals, textvariable=var, font=self.mono_font, state="readonly")
            entry.grid(row=i * 2 + 1, column=0, columnspan=2, sticky="we", ipady=3)
            btn = ttk.Button(vals, text="คัดลอก", width=9,
                             command=lambda v=var, b=None: self.copy(v.get()))
            btn.grid(row=i * 2 + 1, column=2, padx=(6, 0))
            self.ad_values[key] = var
        vals.columnconfigure(0, weight=1)

        self.ad_note = ttk.Label(left, text="ค่าถูกสร้างใหม่ทุกครั้งและไม่ถูกบันทึกลงดิสก์",
                                 style="Sub.TLabel", wraplength=430, justify="left")
        self.ad_note.pack(anchor="w", pady=(12, 0))

        ttk.Label(right, text="สแกนด้วยแอป Authenticator", style="Sub.TLabel").pack(pady=(0, 6))
        self.qr = tk.Canvas(right, width=240, height=240, bg="white",
                            highlightthickness=1, highlightbackground="#ccc")
        self.qr.pack()
        ttk.Button(right, text="แสดง QR ใหม่",
                   command=self.draw_qr_from_state).pack(pady=(8, 0))

    def do_admin(self):
        issuer = self.ad_issuer.get().strip() or "XRay Admin"
        account = self.ad_account.get().strip() or "admin"
        token = core.gen_alnum(40)
        secret = core.b32enc(secrets.token_bytes(20))
        page = "a-%s.html" % core.gen_slug(24)
        uri = core.otpauth_uri(secret, issuer, account)
        now = core.totp(core.b32dec(secret), int(time.time()) // 30)

        self.ad_values["token"].set(token)
        self.ad_values["secret"].set(secret)
        self.ad_values["page"].set(page)
        self.ad_values["uri"].set(uri)
        self._last_uri = uri
        self.draw_qr(uri)
        self.ad_note.config(
            text="รหัสตอนนี้ควรตรงกับแอป: %s %s\n"
                 "ถ้าตรง แปลว่าตั้งค่าถูก — ล้างจอ/ปิดหน้าต่างหลังบันทึกค่าแล้ว" % (now[:3], now[3:]))
        self.status("สร้างชุดค่า admin แล้ว")

    def draw_qr_from_state(self):
        uri = getattr(self, "_last_uri", "")
        if not uri:
            return self.status("กด “สร้างชุดค่า admin” ก่อน")
        self.draw_qr(uri)

    def draw_qr(self, data):
        self.qr.delete("all")
        try:
            import qrcode
        except ImportError:
            self.qr.create_text(120, 100, text="ไม่มีไลบรารี qrcode",
                                font=self.ui_font, fill="#444", width=200)
            self.qr.create_text(120, 140, text="pip install qrcode\nหรือคัดลอกลิงก์ otpauth ไปสร้าง QR เอง",
                                font=(self.ui_font[0], 9), fill="#777", width=210, justify="center")
            return
        q = qrcode.QRCode(border=2, box_size=1)
        q.add_data(data)
        q.make()
        matrix = q.get_matrix()
        n = len(matrix)
        cell = max(2, 240 // n)
        size = n * cell
        self.qr.config(width=size, height=size)
        for y, row in enumerate(matrix):
            for x, on in enumerate(row):
                if on:
                    self.qr.create_rectangle(x * cell, y * cell, (x + 1) * cell, (y + 1) * cell,
                                             fill="black", outline="")

    # ------------------------------------------------------- แท็บ 4: TOTP สด
    def tab_totp(self, f):
        box = ttk.Frame(f, padding=(18, 16, 18, 10))
        box.pack(fill="x")

        ttk.Label(box, text="Secret (base32)").grid(row=0, column=0, sticky="w")
        self.tp_secret = tk.StringVar(value=os.environ.get("XPASS_SECRET", ""))
        self.tp_entry = ttk.Entry(box, textvariable=self.tp_secret, font=self.mono_font, width=40)
        self.tp_entry.grid(row=0, column=1, sticky="we", padx=10, pady=4, ipady=3)
        box.columnconfigure(1, weight=1)

        self.tp_hide = tk.BooleanVar(value=False)
        ttk.Checkbutton(box, text="ซ่อน", variable=self.tp_hide,
                        command=self._toggle_secret).grid(row=0, column=2)

        btns = ttk.Frame(box)
        btns.grid(row=1, column=0, columnspan=3, sticky="w", pady=(10, 0))
        self.tp_start = ttk.Button(btns, text="เริ่มแสดงรหัส", command=self.toggle_totp)
        self.tp_start.pack(side="left")
        self.tp_copy = ttk.Button(btns, text="คัดลอกรหัส",
                                  command=lambda: self.copy(self._totp_code, self.tp_copy))
        self.tp_copy.pack(side="left", padx=6)

        center = ttk.Frame(f, padding=(18, 20, 18, 10))
        center.pack(fill="both", expand=True)
        self.tp_code = ttk.Label(center, text="••• •••", style="Big.TLabel")
        self.tp_code.pack(pady=(10, 14))
        self.tp_bar = ttk.Progressbar(center, maximum=30, length=320)
        self.tp_bar.pack()
        self.tp_sub = ttk.Label(center, text="ใส่ secret แล้วกด “เริ่มแสดงรหัส”", style="Sub.TLabel")
        self.tp_sub.pack(pady=(10, 0))

    def _toggle_secret(self):
        self.tp_entry.config(show="•" * 1 if self.tp_hide.get() else "")

    def toggle_totp(self):
        if self._totp_job is not None:
            self.after_cancel(self._totp_job)
            self._totp_job = None
            self._totp_key = None
            self._totp_code = ""
            self.tp_code.config(text="••• •••")
            self.tp_bar["value"] = 0
            self.tp_sub.config(text="หยุดแล้ว")
            self.tp_start.config(text="เริ่มแสดงรหัส")
            self.status("หยุดแสดงรหัส")
            return

        raw = self.tp_secret.get().strip()
        if not raw:
            self.tp_entry.focus_set()
            return messagebox.showwarning("ต้องมี secret", "ใส่ secret (base32) ก่อนครับ")
        try:
            key = core.b32dec(raw)
            if not key:
                raise ValueError
        except Exception:
            return messagebox.showerror("secret ไม่ถูกต้อง",
                                        "secret ต้องเป็นตัวอักษร A–Z และเลข 2–7 (base32)")
        self._totp_key = key
        self.tp_start.config(text="หยุด")
        self.status("กำลังแสดงรหัส TOTP")
        self._tick()

    def _tick(self):
        now = int(time.time())
        left = 30 - now % 30
        code = core.totp(self._totp_key, now // 30)
        self._totp_code = code
        self.tp_code.config(text="%s %s" % (code[:3], code[3:]))
        self.tp_bar["value"] = left
        self.tp_sub.config(text="เหลืออีก %d วินาที" % left)
        self._totp_job = self.after(200, self._tick)

    # ------------------------------------------------------- แท็บ 5: ผู้ช่วย AI
    def tab_ai(self, f):
        f.columnconfigure(0, weight=1)
        f.rowconfigure(2, weight=1)

        warn = ttk.Label(
            f, text="คำเตือน: แท็บนี้เชื่อมต่ออินเทอร์เน็ต — อย่าพิมพ์รหัสผ่านจริง TOTP secret หรือ API key ลงในช่องแชท",
            foreground="#a15c00", wraplength=720, justify="left", padding=(18, 12, 18, 0))
        warn.grid(row=0, column=0, sticky="ew")

        box = ttk.Frame(f, padding=(18, 8, 18, 6))
        box.grid(row=1, column=0, sticky="ew")
        ttk.Label(box, text="API key").grid(row=0, column=0, sticky="w")
        self.ai_key = tk.StringVar()
        self.ai_key_entry = ttk.Entry(box, textvariable=self.ai_key, show="•",
                                      font=self.mono_font, width=42)
        self.ai_key_entry.grid(row=0, column=1, sticky="we", padx=8, pady=3, ipady=3)
        self.ai_hide = tk.BooleanVar(value=True)
        ttk.Checkbutton(box, text="ซ่อน", variable=self.ai_hide,
                        command=self._ai_toggle_key).grid(row=0, column=2)
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="โมเดล").grid(row=1, column=0, sticky="w")
        self.ai_model = tk.StringVar(value=self.settings.get("last_model") or ai.default_model())
        self.ai_model_box = ttk.Combobox(box, textvariable=self.ai_model,
                                         values=list(ai.MODEL_CHOICES),
                                         font=self.mono_font, width=26, state="normal")
        self.ai_model_box.grid(row=1, column=1, sticky="w", padx=8, pady=3, ipady=3)
        self.ai_model_box.bind("<<ComboboxSelected>>", lambda e: self._ai_update_hint())
        self.ai_model_btn = ttk.Button(box, text="รีเฟรช", width=8,
                                       command=self._ai_refresh_models)
        self.ai_model_btn.grid(row=1, column=2, sticky="w", padx=(0, 8))
        self.ai_hint = ttk.Label(box, text="", style="Sub.TLabel")
        self.ai_hint.grid(row=1, column=3, sticky="e")
        self._ai_update_hint()

        body = ttk.Frame(f, padding=(18, 0, 18, 6))
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        self.ai_chat = tk.Text(body, height=8, wrap="word", font=self.ui_font, relief="solid",
                               borderwidth=1, padx=10, pady=8, spacing3=3, state="disabled")
        self.ai_chat.grid(row=0, column=0, sticky="nsew")
        self.ai_chat.tag_configure("who_you", foreground="#1a4fd6",
                                   font=(self.ui_font[0], 10, "bold"))
        self.ai_chat.tag_configure("who_ai", foreground="#1b7f3b",
                                   font=(self.ui_font[0], 10, "bold"))
        self.ai_chat.tag_configure("err", foreground="#b3261e")
        self.ai_chat.tag_configure("intro", foreground="#5f6368")

        line = ttk.Frame(body)
        line.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.ai_input = tk.Text(line, height=3, wrap="word", font=self.ui_font, relief="solid",
                                borderwidth=1, padx=8, pady=6)
        self.ai_input.pack(side="left", fill="x", expand=True)
        btns = ttk.Frame(line)
        btns.pack(side="left", fill="y", padx=(8, 0))
        self.ai_send_btn = ttk.Button(btns, text="ส่งคำถาม", command=self._ai_send)
        self.ai_send_btn.pack(fill="x")
        self.ai_clear_btn = ttk.Button(btns, text="ล้าง", command=self._ai_clear)
        self.ai_clear_btn.pack(fill="x", pady=(6, 0))

        foot = ttk.Frame(f, padding=(18, 0, 18, 12))
        foot.grid(row=3, column=0, sticky="ew")
        self.ai_status = ttk.Label(foot, text="", style="Sub.TLabel")
        self.ai_status.pack(side="left")
        self.ai_foot_hint = ttk.Label(foot, text="ส่งด้วย Ctrl+Enter", style="Sub.TLabel")
        self.ai_foot_hint.pack(side="right")

        self._ai_line(None, "ถามได้เลย เช่น “TOTP ต่างจากรหัสผ่านอย่างไร” หรือ “ควรเก็บ secret 2FA ที่ไหน”", "intro")

    def _ai_update_hint(self):
        model = self.ai_model.get().strip() or ai.default_model()
        provider = ai.provider_for_model(model)
        env_name = ai.env_key_name(provider)
        if env_name:
            self.ai_hint.config(text="ใช้คีย์จาก %s ในเครื่อง" % env_name)
        else:
            self.ai_hint.config(text="คีย์ไม่ถูกบันทึกลงดิสก์ · %s" % ai.provider_label(provider))

    def _ai_toggle_key(self):
        self.ai_key_entry.config(show="" if not self.ai_hide.get() else "•")

    def _ai_line(self, who, text, tag):
        self.ai_chat.configure(state="normal")
        if self.ai_chat.index("end-1c") != "1.0":
            self.ai_chat.insert("end", "\n")
        if who:
            self.ai_chat.insert("end", who + "\n", tag)
            self.ai_chat.insert("end", text + "\n")
        else:
            self.ai_chat.insert("end", text + "\n", tag)
        self.ai_chat.configure(state="disabled")
        self.ai_chat.see("end")

    def _ai_send(self):
        if self._ai_busy:
            return
        text = self.ai_input.get("1.0", "end").strip()
        if not text:
            self.ai_input.focus_set()
            return
        model = self.ai_model.get().strip() or ai.default_model()
        if self.settings.get("remember_model") and model != self.settings.get("last_model"):
            self.settings["last_model"] = model
            appsettings.save(self.settings)
        provider = ai.provider_for_model(model)
        key = self.ai_key.get().strip() or ai.env_api_key(provider)
        if not key:
            self._ai_line(None, "ผิดพลาด: ยังไม่มี API key ของ %s — ใส่คีย์ด้านบนก่อน หรือตั้งค่า %s"
                          % (ai.provider_label(provider), " / ".join(ai.PROVIDER_ENV_KEYS[provider])), "err")
            self.ai_key_entry.focus_set()
            return
        self.ai_input.delete("1.0", "end")
        self._ai_messages.append({"role": "user", "content": text})
        self._ai_line("คุณ", text, "who_you")
        self._ai_busy = True
        self.ai_send_btn.config(state="disabled")
        self.ai_clear_btn.config(state="disabled")
        self.ai_model_btn.config(state="disabled")
        self.ai_status.config(text="กำลังคิด…")
        self.status("กำลังคิด…")
        snapshot = self._ai_context()
        threading.Thread(target=self._ai_worker, args=(snapshot, key, model, provider),
                         daemon=True).start()
        self.after(100, self._ai_poll)

    def _ai_context(self, limit=12):
        """ส่งเฉพาะบทสนทนาล่าสุด เพื่อคุมจำนวน token"""
        system = [self._ai_messages[0]] if self._ai_messages else []
        rest = [m for m in self._ai_messages[1:] if m.get("role") in ("user", "assistant")]
        return system + rest[-limit:]

    def _ai_worker(self, messages, key, model, provider):
        try:
            reply = ai.chat(messages, key=key, model=model, provider=provider)
        except Exception as exc:
            self._ai_queue.put(("err", str(exc)))
        else:
            self._ai_queue.put(("ok", reply))

    def _ai_refresh_models(self):
        """ดึงรายชื่อโมเดลจริงจาก API แล้วเติมใน combobox"""
        if self._ai_busy:
            return
        model = self.ai_model.get().strip() or ai.default_model()
        provider = ai.provider_for_model(model)
        key = self.ai_key.get().strip() or ai.env_api_key(provider)
        if not key:
            self._ai_line(None, "ผิดพลาด: ใส่ API key ของ %s ก่อนดึงรายการโมเดล"
                          % ai.provider_label(provider), "err")
            self.ai_key_entry.focus_set()
            return
        self._ai_busy = True
        self.ai_send_btn.config(state="disabled")
        self.ai_clear_btn.config(state="disabled")
        self.ai_model_btn.config(state="disabled")
        self.ai_status.config(text="กำลังดึงรายการโมเดล…")
        threading.Thread(target=self._ai_models_worker, args=(key, provider),
                         daemon=True).start()
        self.after(100, self._ai_poll)

    def _ai_models_worker(self, key, provider):
        try:
            models = ai.list_models(key=key, provider=provider)
        except Exception as exc:
            self._ai_queue.put(("models_err", str(exc)))
        else:
            self._ai_queue.put(("models", models))

    def _ai_apply_models(self, models):
        current = self.ai_model.get().strip()
        self.ai_model_box.config(values=models)
        if current:
            self.ai_model.set(current)
        self._ai_update_hint()

    def _ai_poll(self):
        try:
            kind, payload = self._ai_queue.get_nowait()
        except queue.Empty:
            self.after(120, self._ai_poll)
            return
        note = ""
        if kind == "ok":
            self._ai_messages.append({"role": "assistant", "content": payload})
            self._ai_line("AI", payload, "who_ai")
        elif kind == "models":
            self._ai_apply_models(payload)
            note = ("พบ %d โมเดล — เลือกจากรายการได้เลย" % len(payload)
                    if payload else "ไม่พบโมเดลที่ใช้ได้กับคีย์นี้")
        elif kind == "models_err":
            self._ai_line(None, "ผิดพลาด: " + payload, "err")
        else:
            if self._ai_messages and self._ai_messages[-1].get("role") == "user":
                self._ai_messages.pop()
            self._ai_line(None, "ผิดพลาด: " + payload, "err")
        self._ai_busy = False
        self.ai_send_btn.config(state="normal")
        self.ai_clear_btn.config(state="normal")
        self.ai_model_btn.config(state="normal")
        self.ai_status.config(text=note)
        if kind == "ok":
            self.status("ผู้ช่วย AI ตอบกลับแล้ว")
        elif kind == "models":
            self.status(note)
        else:
            self.status("ผู้ช่วย AI ผิดพลาด")

    def _ai_clear(self):
        if self._ai_busy:
            return
        if self.settings.get("confirm_clear") and len(self._ai_messages) > 1:
            if not messagebox.askyesno("ล้างบทสนทนา",
                                       "ต้องการล้างบทสนทนาทั้งหมดหรือไม่?\n(ข้อความจะหายและกู้คืนไม่ได้)"):
                return
        self._ai_messages = [{"role": "system", "content": ai.SYSTEM_PROMPT}]
        self.ai_chat.configure(state="normal")
        self.ai_chat.delete("1.0", "end")
        self.ai_chat.configure(state="disabled")
        self._ai_line(None, "ถามได้เลย เช่น “TOTP ต่างจากรหัสผ่านอย่างไร” หรือ “ควรเก็บ secret 2FA ที่ไหน”", "intro")
        self.ai_status.config(text="")


if __name__ == "__main__":
    App().mainloop()
