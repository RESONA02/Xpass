# เปิดโปรเจกต์เป็นโอเพนซอร์ส และขอใบรับรองลงนามโค้ดฟรี

เอกสารนี้พาไปทีละขั้นตั้งแต่ "repo ยังปิดอยู่" ไปจนถึง "ได้ไฟล์ exe/MSI ที่ลงนามแล้ว
และ Windows ไม่เตือน Unknown publisher"

## สถานะปัจจุบัน

| ข้อกำหนด | สถานะ |
|---|---|
| สัญญาอนุญาต OSI (MIT) | ✅ `LICENSE` (Copyright 2026 XRayTH) |
| ไฟล์ build จากซอร์สได้ | ✅ `tools/build.ps1` + `xpass.spec` |
| CI build อัตโนมัติ | ✅ `.github/workflows/build.yml` |
| เอกสาร contribut / security / conduct | ✅ `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` |
| ไม่มีความลับในประวัติ git | ✅ ตรวจแล้ว (ไม่มี API key / private key) |
| **repo เป็น public** | ❌ ยังปิดอยู่ (github.com/RESONA02/Xpass ตอบ 404) |
| ใบรับรองลงนามโค้ด | ❌ ยังไม่มี |
| Defender false positive | ยังไม่ส่งตรวจ |

## ทำไมต้องเปิดเป็น public

Windows ไม่ได้บล็อกเพราะเรื่องสัญญาอนุญาต แต่เพราะไฟล์ `.exe` / `.msi` **ไม่ได้ลงนามดิจิทัล**
การจะได้ใบรับรองลงนามแบบไม่ต้องจ่ายเงิน ต้องผ่านโปรแกรมสำหรับโอเพนซอร์ส ซึ่งบังคับว่า
**ซอร์สโค้ดต้องเปิดให้สาธารณะเข้าถึงได้** และ build ซ้ำได้จาก repo

ทางเลือกที่เหมาะกับโปรเจกต์นี้ที่สุดคือ **SignPath Foundation** — ให้ใบรับรองลงนามฟรี
กับโปรเจกต์โอเพนซอร์ส (ไม่จำกัดจำนวนไฟล์ แต่มีเงื่อนไขเรื่องใบอนุญาตและความเป็นโอเพนซอร์สจริง)

## ขั้นที่ 1 — เปิด repo เป็น public

ทำในเครื่องนี้ (ต้องมีสิทธิ์ push):

```powershell
cd C:\Users\XRAY\Downloads\App

# 1) ตรวจว่าไม่มีไฟล์เกินจำเป็นติดไปด้วย
git status

# 2) commit งานที่ค้างอยู่
git add -A
git commit -m "docs: เพิ่มเอกสารโอเพนซอร์สและ CI build"

# 3) push ขึ้น GitHub
git push origin main
```

จากนั้นเปลี่ยน visibility บนเว็บ (ทำผ่าน API ไม่ได้ถ้าไม่มี token):

1. เปิด https://github.com/RESONA02/Xpass/settings
2. เลื่อนลงไปที่ **Danger Zone** → **Change repository visibility** → **Change to public**
3. พิมพ์ชื่อ repo เพื่อยืนยัน

> **ก่อนกด public ตรวจอีกครั้ง:** ไม่มีไฟล์ `.env`, `*.pfx`, `*.key`, API key หรือโฟลเดอร์ทดสอบส่วนตัว
> ติดอยู่ในประวัติ commit (ปัจจุบันตรวจแล้วไม่พบ แต่ถ้าเพิ่มไฟล์ใหม่ให้เช็กซ้ำ)

หลังเปิด public แล้ว ใส่คำอธิบายและ topics ให้ค้นหาเจอ:

```
Description: Offline password / TOTP / secret-name generator for Windows, with CLI, Qt and tkinter UIs
Topics: python, password-generator, totp, 2fa, pyside6, tkinter, offline, windows, security-tools
```

## ขั้นที่ 2 — สมัคร SignPath Foundation

สมัครที่ https://signpath.org/ (ปุ่ม *Apply for free signing*) ใช้บัญชี GitHub ของคุณ

สิ่งที่ต้องเตรียม:

- URL ของ repo สาธารณะ
- ใบอนุญาต (MIT) และลิงก์ไฟล์ `LICENSE`
- คำอธิบายสั้น ๆ ว่าโปรเจกต์ทำอะไร
- ชื่อผู้ดูแล (maintainer) ที่ตรงกับบัญชี GitHub
- ยืนยันว่าซอร์สทั้งหมดเปิดเผย ไม่มี binary ที่มาปิด (ฟอนต์ที่แนบมาเป็น SIL OFL — ใส่หมายเหตุไว้)

### ข้อความกรอกฟอร์ม (คัดลอกไปใช้ได้)

**Project name**

```
xpass
```

**Repository URL**

```
https://github.com/RESONA02/Xpass
```

**License**

```
MIT (OSI-approved) — see LICENSE
```

**Short description**

```
xpass is a fully offline desktop utility for Windows that generates strong passwords,
TOTP (2FA) codes and secret file/URL names. It ships three interfaces (CLI, PySide6,
tkinter) and an optional AI assistant tab that talks to OpenAI or Google Gemini only
when the user supplies their own API key. Everything else runs locally; no telemetry,
no network calls, no account system.
```

**Why do you need code signing?**

```
The Windows builds are produced with PyInstaller and packaged as an MSI. Because the
binaries are unsigned, users get SmartScreen "Windows protected your PC" warnings and
"Unknown publisher" prompts, and Microsoft Defender occasionally flags the PyInstaller
bootloader as a false positive. xpass handles passwords and 2FA secrets, so users are
rightly cautious about running an unverified binary — an invalid or missing signature
is a real barrier to adoption. Signing lets users verify that the download really comes
from this project and was not tampered with.
```

**How is the project built?**

```
Fully from source on windows-latest GitHub Actions runners
(.github/workflows/build.yml):

1. pip install PySide6 pyinstaller
2. python xpass.py selftest            (RFC 6238 test vectors)
3. python tools/make_icon.py
4. PyInstaller --onedir --windowed --add-data assets/fonts xpass_qt.py
5. WiX Toolset 3: heat + candle + light -> xpass-<version>.msi

No prebuilt binaries are committed to the repository. The only bundled third-party
assets are the IBM Plex Sans Thai and JetBrains Mono fonts, distributed under the
SIL Open Font License 1.1 (license texts are in assets/fonts/OFL-*.txt).
```

**Anything else the reviewers should know?**

```
The application is a security tool for end users, so a verifiable signature matters
more than usual. The project is maintained by a single author (@RESONA02), is not
commercialised, and has no paid tier. Releases will be signed for both xpass.exe and
the MSI installer, with RFC 3161 timestamps.
```

## ขั้นที่ 3 — หลังได้รับอนุมัติ

1. ติดตั้ง **SignPath GitHub App** ให้ repo `RESONA02/Xpass`
2. ใน SignPath web UI สร้าง:
   - Project slug: `xpass`
   - Signing policy: `release-signing` (manual approval สำหรับ tag)
   - Artifact configuration: `xpass` — mapping ไฟล์ใน artifact
     `xpass-unsigned` เข้า `dist/xpass/xpass.exe` และ `installer/*.msi`
3. ตั้งค่าใน GitHub repo → Settings → Secrets and variables → Actions:

| ชนิด | ชื่อ | ค่า |
|---|---|---|
| Secret | `SIGNPATH_API_TOKEN` | token จากหน้า User settings ของ SignPath |
| Variable | `SIGNPATH_ORGANIZATION_ID` | UUID ขององค์กรใน SignPath |

4. ออก release:

```powershell
git tag v1.0.2
git push origin v1.0.2
```

workflow `build.yml` จะ build → ส่งลงนาม → รอผล → แนบไฟล์ที่ลงนามแล้วกับ GitHub Release
(ถ้ายังไม่ตั้งค่า SignPath job `sign` จะถูกข้าม และ build ยังทำงานปกติ)

## ขั้นที่ 4 — ตรวจสอบว่าไฟล์ลงนามจริง

```powershell
Get-AuthenticodeSignature .\xpass.exe | Format-List Status, StatusMessage, SignerCertificate
```

ต้องได้ `Status : Valid` และมีชื่อผู้ลงนาม ไม่ใช่ `NotSigned`

ถ้า Defender ยังจับอยู่ ให้ส่งไฟล์ที่ https://www.microsoft.com/en-us/wdsi/filesubmission
เลือก "Software developer" แล้วระบุว่าเป็น false positive ของแอปที่ลงนามแล้ว

## ทางเลือกสำรอง

| ทาง | ค่าใช้จ่าย | หมายเหตุ |
|---|---|---|
| **SignPath Foundation** | ฟรี | ต้องเป็น public repo + ผ่านการตรวจ (แนะนำ) |
| Certum Open Source Code Signing | ~€30–80/ปี | ถูกกว่า commercial มาก ต้องยื่นหลักฐานว่าเป็น OSS |
| OV Code Signing | ~$200–400/ปี | ใช้ได้ทั่วไป แต่ SmartScreen ต้องสะสมชื่อเสียง |
| EV Code Signing | ~$300–500/ปี | ได้ชื่อเสียงทันที ต้องใช้ hardware token |
| Self-signed | ฟรี | ใช้ได้เฉพาะเครื่องที่ติดตั้ง root cert เอง — **แจกให้คนอื่นไม่ได้** |

## หมายเหตุสำหรับผู้ใช้ที่ยังเจอคำเตือน

จนกว่า release จะลงนามแล้ว ผู้ใช้สามารถ:

- ดาวน์โหลดซอร์สแล้วรัน `open-xpass.bat` (ไม่ต้องใช้ exe)
- ถ้าเจอ "Windows protected your PC" → **More info** → **Run anyway**
- หลีกเลี่ยงการปิด Smart App Control ทั้งระบบ เพราะปิดแล้วเปิดกลับไม่ได้จนกว่าจะลง Windows ใหม่
