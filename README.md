# xpass

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![build](https://github.com/RESONA02/Xpass/actions/workflows/build.yml/badge.svg)](https://github.com/RESONA02/Xpass/actions/workflows/build.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

เครื่องมือสร้างรหัสผ่าน / รหัส 2FA (TOTP) / ชื่อหน้าลับ แบบ **ออฟไลน์** (ยกเว้นแท็บผู้ช่วย AI ที่เป็นออปชัน)
โหมดหลักคำนวณในเครื่องทั้งหมด ไม่เขียนไฟล์โดยอัตโนมัติ ยกเว้นไฟล์ค่าตั้งของผู้ใช้ (`settings.json`) ซึ่งเก็บเฉพาะ
ฟอนต์ ขนาดตัวอักษร ธีม และปุ่มลัด — ไม่มีรหัสผ่าน TOTP secret หรือ API key อยู่ในไฟล์นั้น
(จะเขียนไฟล์ผลลัพธ์ก็ต่อเมื่อผู้ใช้สั่ง บันทึก / ส่งออก / พิมพ์ เอง)

## ไฟล์ในโปรเจกต์

| ไฟล์ | คำอธิบาย |
|---|---|
| `xpass.py` | แกนหลัก + CLI (ใช้ไลบรารีมาตรฐานของ Python เท่านั้น) |
| `xpass_qt.py` | UI เดสก์ท็อป ธีมมืด/สว่าง ด้วย PySide6 (แนะนำ) |
| `xpass_gui.py` | UI เดสก์ท็อปด้วย tkinter (ไม่ต้องติดตั้งอะไรเพิ่ม) |
| `xpass_fonts.py` | โหลด/เลือกฟอนต์ไทย–อังกฤษให้ทั้งสอง UI |
| `xpass_settings.py` | อ่าน/เขียนค่าตั้งของผู้ใช้ (ฟอนต์ / ขนาด / ปุ่มลัด) — ไม่เก็บข้อมูลลับ |
| `xpass_ai.py` | ไคลเอนต์ AI (stdlib) — OpenAI + Google Gemini สำหรับแท็บผู้ช่วย AI |
| `demo/chat_demo.py` | ตัวอย่างเรียก OpenAI ด้วย `openai` SDK (ทดสอบคีย์, streaming, จัดการ error) |
| `open-xpass.bat` | ดับเบิลคลิกเพื่อเปิดแอป (เลือก Qt ก่อน ถ้าไม่มีจึงใช้ tkinter) |
| `installer/Product.wxs` | สคริปต์ตัวติดตั้ง MSI (WiX) |
| `xpass.iss` | สคริปต์ตัวติดตั้ง Inno Setup (ทางเลือก) |
| `tools/` | สคริปต์สร้างไอคอน / build exe / build MSI |

## การใช้งาน

### CLI

```powershell
python xpass.py pw            # รหัสผ่าน 20 ตัวอักษร
python xpass.py pw 32 -a      # 32 ตัว, ตัดตัวที่อ่านสับสน Il1O0o
python xpass.py pw -n 5       # สร้าง 5 ชุด
python xpass.py name          # ชื่อไฟล์/URL ลับ
python xpass.py admin         # ADMIN_TOKEN + ADMIN_TOTP_SECRET + ชื่อหน้า admin (+ QR)
python xpass.py totp          # รหัส 2FA สด (นับถอยหลัง)
python xpass.py verify 123456 # ตรวจรหัส TOTP (±1 ช่วงเวลา)
python xpass.py selftest      # ทดสอบกับเวกเตอร์ RFC 6238
```

### GUI

```powershell
python xpass_qt.py    # ต้องมี PySide6
python xpass_gui.py   # tkinter อย่างเดียว
```

หรือดับเบิลคลิก `open-xpass.bat`

## เมนู (เฉพาะ UI Qt)

แถบเมนูด้านบนแบ่งเป็น 5 หมวด และใช้ปุ่มลัดได้ทันที:

| เมนู | รายการหลัก | ปุ่มลัด |
|---|---|---|
| **ไฟล์ (File)** | สร้างชุดใหม่, บันทึกผลลัพธ์, ส่งออกทั้งหมด, นำเข้า secret TOTP, พิมพ์, ปิด/ออก | `Ctrl+N` · `Ctrl+S` · `Ctrl+Shift+S` · `Ctrl+O` · `Ctrl+P` · `Ctrl+Q` |
| **แก้ไข (Edit)** | เลิกทำ, ทำซ้ำ, ตัด/คัดลอก/วาง, เลือกทั้งหมด, ค้นหา, แทนที่ | `Ctrl+Z` · `Ctrl+Y` · `Ctrl+X/C/V` · `Ctrl+A` · `Ctrl+F` · `Ctrl+H` |
| **มุมมอง (View)** | ซูมเข้า/ออก, ขนาดปกติ, เต็มจอ, แถบด้านข้าง, ธีมมืด/สว่าง | `Ctrl++` · `Ctrl+-` · `Ctrl+0` · `F11` · `Ctrl+B` |
| **ตั้งค่า (Settings)** | การตั้งค่า, บันทึกค่าตั้ง, บัญชีผู้ใช้, เปิดโฟลเดอร์ค่าตั้ง | `Ctrl+,` |
| **ช่วยเหลือ (Help)** | คู่มือการใช้งาน, ตรวจสอบการอัปเดต, เกี่ยวกับ | `F1` |

- **บันทึก / ส่งออก** เขียนผลลัพธ์ของแท็บปัจจุบันหรือทุกแท็บเป็นไฟล์ `.txt` / `.md`
- **นำเข้า secret TOTP** อ่านไฟล์ข้อความหรือลิงก์ `otpauth://` แล้วเริ่มแสดงรหัสในแท็บ TOTP
- **ค้นหา / แทนที่** ทำงานกับข้อความในแท็บปัจจุบันและช่องที่แก้ไขได้
- **บัญชีผู้ใช้** เป็นเพียงหน้าข้อมูล — แอปไม่มีระบบบัญชีหรือคลาวด์
- **ธีมสว่าง/มืด** เมื่อสลับจากเมนูมุมมองจะบันทึกอัตโนมัติ (ถ้าเปลี่ยนในหน้าตั้งค่า ให้กด “บันทึก”)
  ส่วนการซูมมีผลทันทีแต่ต้องกด “บันทึก” ในหน้าตั้งค่าเพื่อเก็บถาวร

## ฟอนต์

โปรแกรมแนบฟอนต์มาใน `assets/fonts` และโหลดตอนเปิดแอป — ไม่ต้องติดตั้งลง Windows:

- **IBM Plex Sans Thai** — ข้อความ UI ภาษาไทยและอังกฤษ
- **JetBrains Mono** — รหัสผ่าน รหัส TOTP และค่าที่คัดลอก

ถ้าไม่พบไฟล์ฟอนต์ โปรแกรมจะถอยไปใช้ฟอนต์ที่ติดตั้งในเครื่องโดยอัตโนมัติ
(`Segoe UI Variable` → `Segoe UI` → `Leelawadee UI`) และเปลี่ยนเองได้ผ่านตัวแปรสภาพแวดล้อม:

```powershell
$env:XPASS_FONT = "Sarabun"          # ฟอนต์ UI
$env:XPASS_MONO_FONT = "Consolas"    # ฟอนต์ mono
python xpass_qt.py
```

> ในแอปมีหน้า **“ตั้งค่า”** ให้เลือกฟอนต์และขนาดได้โดยไม่ต้องใช้ตัวแปรสภาพแวดล้อม
> (ค่าที่เลือกในหน้า “ตั้งค่า” มีผลเหนือตัวแปรสภาพแวดล้อม)

สัญญาอนุญาตฟอนต์ (SIL OFL 1.1) อยู่ใน `assets/fonts/OFL-*.txt`
ตัวติดตั้ง MSI และ exe ที่ build ใหม่จะแนบฟอนต์ไปด้วยอัตโนมัติ

## ตั้งค่า (แท็บ “ตั้งค่า”)

เปิดแท็บ **“ตั้งค่า”** ในแอป (ทั้ง Qt และ tkinter) เพื่อปรับค่าต่อไปนี้ — **มีผลทันที**
แล้วกด **“บันทึก”** เพื่อเก็บไว้ใช้ครั้งถัดไป:

| หัวข้อ | ตัวเลือก |
|---|---|
| ฟอนต์ UI / ฟอนต์รหัสผ่าน | เลือกจากฟอนต์ที่ติดตั้งในเครื่อง |
| ขนาดตัวอักษร | 80% – 150% |
| ธีม | มืด (Dark) หรือสว่าง (Light) — เฉพาะ UI Qt |
| ปุ่มส่งแชท AI | `Ctrl+Enter` (Enter ขึ้นบรรทัดใหม่) หรือ `Enter` (Shift+Enter ขึ้นบรรทัดใหม่) |
| สลับแท็บ | `Ctrl+1` … `Ctrl+6` |
| สร้าง/เริ่มใหม่ | `F5` ในแท็บปัจจุบัน |
| คัดลอกอัตโนมัติ | คัดลอกรหัสผ่านที่สร้างทันที |
| ยืนยันก่อนล้างแชท | ถามก่อนล้างบทสนทนา AI |
| จำโมเดล AI | เปิดแท็บ AI ครั้งถัดไปใช้โมเดลล่าสุด |

ค่าตั้งเก็บเป็น JSON ที่:

```
%APPDATA%\xpass\settings.json
```

เปลี่ยนที่เก็บได้ด้วย `$env:XPASS_CONFIG_DIR = "D:\my-config"` (มีประโยชน์ตอนทดสอบ)
ถ้าไฟล์เสียหายหรือเขียนไม่ได้ แอปจะใช้ค่าเริ่มต้นและทำงานต่อได้ตามปกติ

**ไฟล์นี้เก็บเฉพาะค่าตั้ง ไม่มีรหัสผ่าน TOTP secret หรือ API key** — ค่าที่สร้างและคีย์ยังอยู่ใน
หน่วยความจำเท่านั้น ปุ่ม “คืนค่าเริ่มต้น” จะยังไม่เขียนลงดิสก์จนกว่าจะกด “บันทึก”

## ผู้ช่วย AI (ออปชัน)

แท็บ **“ผู้ช่วย AI”** รองรับ **OpenAI** และ **Google Gemini** — เลือกได้จาก drop-down
“โมเดล” ในแท็บ (ขึ้นต้นด้วย `gemini…` = Google, `gpt…` = OpenAI) และพิมพ์ชื่อโมเดลอื่นเองได้
เป็นแท็บเดียวของโปรแกรมที่เชื่อมต่ออินเทอร์เน็ต — แท็บอื่นทั้งหมดยังคำนวณในเครื่อง

- ใส่ API key ในช่องของแท็บ (เก็บในหน่วยความจำเท่านั้น ไม่บันทึกลงดิสก์)
  หรือตั้งค่า environment ก่อนเปิดแอป:

```powershell
$env:OPENAI_API_KEY = "sk-..."           # คีย์ OpenAI
$env:GEMINI_API_KEY = "AIza..."          # คีย์ Google AI Studio (หรือ GOOGLE_API_KEY)
$env:XPASS_AI_PROVIDER = "gemini"        # ผู้ให้บริการเริ่มต้น: openai | gemini
$env:XPASS_AI_MODEL = "gemini-3.8-flash" # โมเดลเริ่มต้น (ถ้าไม่ใส่จะใช้ตามผู้ให้บริการ)
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"  # รองรับ endpoint ที่เข้ากันได้
$env:GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
python xpass_qt.py
```

- ไม่ต้องติดตั้ง SDK — ใช้ `urllib` จาก stdlib (ผู้ให้บริการเลือกอัตโนมัติจากชื่อโมเดล)
- ข้อความที่พิมพ์ในแชทจะถูกส่งไปยังผู้ให้บริการที่เลือก จึง**ห้ามพิมพ์รหัสผ่านจริง TOTP secret หรือ API key**
- โปรแกรมจะไม่ส่งค่าที่สร้างในแท็บอื่นไปให้ AI โดยอัตโนมัติ
- ถ้าไม่ใส่ชื่อโมเดล ระบบจะใช้ `gemini-3.8-flash` สำหรับ Gemini และ `gpt-4o-mini` สำหรับ OpenAI
- ปุ่ม **“รีเฟรช”** ข้างช่องโมเดลจะดึงรายการโมเดลที่คีย์นั้นใช้ได้จริงจาก API (ช่วยเมื่อ Google/OpenAI ออกรุ่นใหม่หรือปิดรุ่นเก่า)
- โมเดลตระกูล Gemini 2.5 ถูกจำกัดเฉพาะผู้ใช้เดิม — ถ้าเจอ 404 ให้เลือกรุ่น 3.x ขึ้นไป

### ทดสอบคีย์ด้วยสคริปต์ตัวอย่าง

`demo/chat_demo.py` เป็นตัวอย่างแยกต่างหากที่ใช้ `openai` SDK จริง (คนละตัวกับ `xpass_ai.py`)
ไว้เช็กว่าคีย์ใช้งานได้ และดูวิธีเขียนแบบ streaming / จัดการ error — ลบทิ้งได้โดยไม่กระทบแอป

```powershell
pip install openai                       # ครั้งเดียว
$env:OPENAI_API_KEY = "sk-..."           # คีย์อ่านจาก environment เท่านั้น
python demo\chat_demo.py                 # ถามคำถามตั้งต้น
python demo\chat_demo.py "คำถามของคุณ"
python demo\chat_demo.py --stream        # พิมพ์คำตอบทีละคำ
python demo\chat_demo.py --model gpt-4o --temperature 0.2
```

คีย์ต้องมีเครดิตใน Billing ของ OpenAI ด้วย ไม่งั้นจะได้ `429 insufficient_quota`
(API แยกจาก ChatGPT Plus)

## ติดตั้งเป็นแอป (Windows)

มีตัวติดตั้ง **MSI** ที่ติดตั้งแบบ per-user (ไม่ต้องใช้สิทธิ์ admin)

```
installer\xpass-1.0.1.msi
```

- ดับเบิลคลิกแล้วทำตามขั้นตอน → ได้ไอคอนบน Desktop และ Start Menu
- ติดตั้งไว้ที่ `%LOCALAPPDATA%\Programs\xpass`
- ถอนได้จาก Settings → Apps → xpass
- ติดตั้งเงียบ ๆ: `msiexec /i installer\xpass-1.0.1.msi /qn`

แบบพกพา (ไม่ต้องติดตั้ง): `dist\xpass\xpass.exe`

> **Windows เตือน "Windows protected your PC" หรือ "Unknown publisher"?**
> ไฟล์ที่ build เองยังไม่ได้ลงนามดิจิทัล (code signing) จึงโดน SmartScreen —
> ไม่ใช่เพราะตัวโปรแกรมมีปัญหา ถ้าเจอ ให้กด **More info → Run anyway**
> หรือใช้วิธีรันจากซอร์ส (`open-xpass.bat`) แทน
> อ่านเพิ่มที่ [docs/code-signing.md](docs/code-signing.md)

### build เอง

```powershell
pip install PySide6 pyinstaller
powershell -ExecutionPolicy Bypass -File tools\build.ps1
```

ต้องมี **WiX Toolset 3** แตกไว้ที่ `tools\wix` (โหลด `wix314-binaries.zip`) สำหรับสร้าง MSI

> หมายเหตุ: สคริปต์ `xpass.iss` (Inno Setup) ใช้ได้บนเครื่องทั่วไป แต่จะล้มเหลวถ้าระบบมี
> Application Control policy ที่บล็อกการรัน exe จากโฟลเดอร์ Temp (`Error 4551`) — กรณีนั้นให้ใช้ MSI

## การติดตั้ง (ไม่บังคับ)

แกนหลักใช้ stdlib ล้วน จึงไม่ต้องติดตั้งอะไรเลย

```powershell
pip install PySide6   # สำหรับ UI เวอร์ชัน Qt
pip install qrcode    # สำหรับแสดง QR
```

## ความปลอดภัย

- ใช้ `secrets` ของระบบปฏิบัติการเป็นแหล่งสุ่ม (ไม่ใช่ `random`)
- รหัสผ่านที่สร้างบังคับให้มีครบทุกคลาสอักขระ
- การตรวจรหัส TOTP ใช้ `hmac.compare_digest` (กัน timing attack)
- ค่าที่ generate ไม่ถูกบันทึกอัตโนมัติ — จะเขียนลงไฟล์ก็ต่อเมื่อผู้ใช้สั่ง “บันทึก / ส่งออก / พิมพ์” เอง
- แอปเขียนไฟล์เองเพียงไฟล์เดียวคือ `%APPDATA%\xpass\settings.json` (ฟอนต์/ขนาด/ธีม/ปุ่มลัด) — ไม่มีข้อมูลลับ
  (ไฟล์ผลลัพธ์จะถูกเขียนก็ต่อเมื่อผู้ใช้สั่งบันทึก/ส่งออก/พิมพ์)
- API key ที่พิมพ์ในแท็บ AI อยู่ในหน่วยความจำเท่านั้น ไม่ถูกเขียนลงไฟล์ค่าตั้ง
- โหมดหลัก (รหัสผ่าน / ชื่อหน้า / admin / TOTP) ไม่มีการเชื่อมต่อเครือข่าย
- แท็บ “ผู้ช่วย AI” เท่านั้นที่ส่งข้อความไปยัง OpenAI และจะไม่ส่งค่าที่โปรแกรมสร้างให้โดยอัตโนมัติ

## สัญญาอนุญาต

เผยแพร่ภายใต้ [MIT License](LICENSE) — Copyright (c) 2026 XRayTH

## การมีส่วนร่วม

- [CONTRIBUTING.md](CONTRIBUTING.md) — เริ่มพัฒนา, แนวทางโค้ด, การส่ง PR
- [SECURITY.md](SECURITY.md) — รายงานช่องโหว่ (ห้ามเปิด issue สาธารณะ)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — แนวปฏิบัติของชุมชน
- [docs/code-signing.md](docs/code-signing.md) — ทำไม Windows เตือน และวิธีขอใบรับรองลงนามโค้ดฟรีสำหรับโปรเจกต์โอเพนซอร์ส

ฟอนต์ที่แนบมา (IBM Plex Sans Thai, JetBrains Mono) อยู่ภายใต้ SIL Open Font License 1.1
ดูข้อความสัญญาที่ `assets/fonts/OFL-*.txt`
