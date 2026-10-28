# xpass

เครื่องมือสร้างรหัสผ่าน / รหัส 2FA (TOTP) / ชื่อหน้าลับ แบบ **ออฟไลน์ล้วน**
คำนวณในเครื่องทั้งหมด ไม่เชื่อมต่ออินเทอร์เน็ต ไม่เขียนไฟล์ ไม่เก็บค่าใด ๆ

## ไฟล์ในโปรเจกต์

| ไฟล์ | คำอธิบาย |
|---|---|
| `xpass.py` | แกนหลัก + CLI (ใช้ไลบรารีมาตรฐานของ Python เท่านั้น) |
| `xpass_qt.py` | UI เดสก์ท็อป ธีมมืด ด้วย PySide6 (แนะนำ) |
| `xpass_gui.py` | UI เดสก์ท็อปด้วย tkinter (ไม่ต้องติดตั้งอะไรเพิ่ม) |
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

## ติดตั้งเป็นแอป (Windows)

มีตัวติดตั้ง **MSI** ที่ติดตั้งแบบ per-user (ไม่ต้องใช้สิทธิ์ admin)

```
installer\xpass-1.0.0.msi
```

- ดับเบิลคลิกแล้วทำตามขั้นตอน → ได้ไอคอนบน Desktop และ Start Menu
- ติดตั้งไว้ที่ `%LOCALAPPDATA%\Programs\xpass`
- ถอนได้จาก Settings → Apps → xpass
- ติดตั้งเงียบ ๆ: `msiexec /i installer\xpass-1.0.0.msi /qn`

แบบพกพา (ไม่ต้องติดตั้ง): `dist\xpass\xpass.exe`

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
- ค่าที่ generate ไม่ถูกบันทึกลงดิสก์ — คัดลอกหรือจดเก็บเองทันที
- ไม่มีโค้ดส่วนใดเปิดการเชื่อมต่อเครือข่าย

## สัญญาอนุญาต

MIT
