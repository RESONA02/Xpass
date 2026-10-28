# การมีส่วนร่วมพัฒนา (Contributing)

ขอบคุณที่สนใจช่วยพัฒนา xpass! เอกสารนี้สรุปวิธีเริ่มต้นและสิ่งที่ควรรู้ก่อนส่ง PR

## ก่อนเริ่ม

- โปรเจกต์นี้ใช้สัญญาอนุญาต **MIT** — การส่งโค้ดเข้ามาถือว่าคุณอนุญาตให้เผยแพร่ผลงานนั้นภายใต้สัญญาเดียวกัน
- เรื่องความปลอดภัย: **อย่าเปิด issue สาธารณะ** — อ่าน [SECURITY.md](SECURITY.md) ก่อน
- ถ้าเป็นการเปลี่ยนแปลงใหญ่ (โครงสร้าง UI, ระบบใหม่, dependency ใหม่) เปิด issue คุยก่อนเพื่อลดงานที่ต้องแก้

## เตรียมเครื่อง

ต้องมี Python 3.10 ขึ้นไป

```powershell
git clone https://github.com/RESONA02/Xpass.git
cd Xpass

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install PySide6      # UI เวอร์ชัน Qt (แนะนำ)
pip install qrcode       # แสดง QR ในแท็บ admin
```

แกนหลัก (`xpass.py`, `xpass_ai.py`) ใช้ stdlib ล้วน จึงรันได้โดยไม่ต้องติดตั้งอะไรเพิ่ม

## รันและทดสอบ

```powershell
python xpass.py selftest        # เวกเตอร์ RFC 6238 — ต้องผ่านก่อนส่ง PR
python xpass.py pw              # ทดสอบ CLI
python xpass_qt.py              # ทดสอบ UI Qt
python xpass_gui.py             # ทดสอบ UI tkinter
```

ถ้าแก้ส่วน UI ควรลองทั้งสองเวอร์ชัน (Qt และ tkinter) เพราะใช้โค้ดแกนร่วมกัน

## แนวทางการเขียนโค้ด

- **ภาษา:** ข้อความใน UI, คอมเมนต์ และเอกสารใช้ภาษาไทย ตัวระบุในโค้ด (ชื่อตัวแปร/ฟังก์ชัน) ใช้ภาษาอังกฤษ
- **สไตล์:** ตามโค้ดเดิม — 4 spaces, บรรทัดไม่เกิน ~100 ตัวอักษร, ไม่ต้องเพิ่ม linter ใหม่ถ้าไม่จำเป็น
- **dependency:** พยายามหลีกเลี่ยง dependency ใหม่ในแกนหลัก (`xpass.py` ต้องรันด้วย stdlib ได้เสมอ)
- **ความปลอดภัย:** ใช้ `secrets` เท่านั้น ห้ามใช้ `random` กับข้อมูลที่ต้องเดายาก
  และห้ามเขียนรหัสผ่าน/TOTP secret/API key ลงดิสก์หรือ log
- **ความเป็นส่วนตัว:** ห้ามเพิ่มการเชื่อมต่อเครือข่ายในแท็บที่ไม่ใช่ "ผู้ช่วย AI"

## commit message

ใช้รูปแบบสั้น ๆ ที่อ่านแล้วรู้ว่าเปลี่ยนอะไร ภาษาไทยหรืออังกฤษก็ได้:

```
เพิ่มปุ่มคัดลอกรหัสในแท็บ TOTP
fix: TOTP หมดอายุแล้วไม่รีเฟรช
docs: อธิบายวิธี build MSI
```

## การส่ง PR

1. แตกแขนงจาก `main` (`git switch -c fix/totp-refresh`)
2. แก้โค้ด + รัน `python xpass.py selftest`
3. อัปเดต README หรือเอกสารที่เกี่ยวข้องถ้าพฤติกรรมเปลี่ยน
4. เปิด PR อธิบายว่า **ทำอะไร / ทำไม** และแนบภาพหน้าจอถ้าเป็นงาน UI

PR จะถูกตรวจโดย GitHub Actions (`.github/workflows/build.yml`) ซึ่ง build ทั้ง exe และ MSI
ถ้า workflow แดง ให้แก้ก่อนขอ review

## การออกรุ่น (เฉพาะผู้ดูแล)

```powershell
powershell -ExecutionPolicy Bypass -File tools\build.ps1
git tag v1.0.2
git push origin v1.0.2
```

 pushing tag `v*` จะทำให้ CI ลงนามไฟล์ (ถ้าตั้งค่า SignPath แล้ว) และแนบไฟล์กับ GitHub Release โดยอัตโนมัติ
