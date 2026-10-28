# xpass for Android

แอป Android ของ **xpass** เขียนด้วย **Kotlin + Jetpack Compose**
ทำงานออฟไลน์เป็นหลัก (แท็บ AI เท่านั้นที่ต่ออินเทอร์เน็ต) และเพิ่มสิ่งที่เดสก์ท็อปไม่มี:
**vault 2FA ที่เข้ารหัสไว้ในเครื่อง**

| | |
|---|---|
| Package | `th.xrayth.xpass` |
| minSdk | 26 (Android 8.0) |
| targetSdk | 35 (Android 15) |
| ภาษา | Kotlin 2.0.21 · Compose BOM 2024.12.01 |
| Gradle / AGP | 8.9 · 8.7.3 |
| JDK | 17 |

---

## ติดตั้งทันที (ไม่ต้อง build)

มีไฟล์ APK ที่ build แล้วอยู่ในโปรเจกต์:

```
installer/xpass-android-1.0.0.apk      # 2.9 MB — ลงนามด้วย debug key
```

คัดลอกไปที่มือถือ → เปิดไฟล์ → อนุญาต “ติดตั้งจากแหล่งที่ไม่รู้จัก”
หรือใช้ adb:

```powershell
adb install -r installer/xpass-android-1.0.0.apk
```

> APK นี้ลงนามด้วย debug key ใช้ติดตั้งทดสอบได้ แต่ **อัปโหลดขึ้น Play Store ไม่ได้**
> ถ้าจะเผยแพร่ ให้สร้าง keystore ของตัวเองแล้ว build ใหม่ (หัวข้อถัดไป)

---

## ฟีเจอร์

| แท็บ | ทำอะไรได้ |
|---|---|
| **รหัสผ่าน** | สร้างรหัส 8–128 ตัว พร้อมมิเตอร์ entropy, ตัวเลือกสัญลักษณ์, ตัดตัวอ่านสับสน `Il1O0o`, คัดลอก |
| **2FA** | เก็บบัญชี TOTP ใน vault, เพิ่มด้วยการวาง secret / ลิงก์ `otpauth://` / สแกน QR, แสดงรหัสสดพร้อมวงนับถอยหลัง, คัดลอก, แสดง QR สำรอง, แก้ไข/ลบ |
| **ชื่อหน้า** | สร้าง slug สุ่มสำหรับชื่อไฟล์/URL ลับ และชุดค่า admin (`ADMIN_TOKEN`, `ADMIN_TOTP_SECRET`, ชื่อหน้า) พร้อม QR |
| **AI** | ผู้ช่วย AI (OpenAI + Google Gemini) ใช้ `HttpURLConnection` ไม่ต้องมี SDK, รีเฟรชรายการโมเดลได้ |
| **ตั้งค่า** | ธีม มืด/สว่าง/ตามระบบ, ขนาดตัวอักษร 80–150%, PIN, ไบโอเมตริก, ล็อกอัตโนมัติ, ล้างข้อมูล |

---

## ความปลอดภัย

- **เข้ารหัสทั้ง vault** ด้วย AES-256-GCM
- **master key** สุ่ม 32 ไบต์ เก็บในหน่วยความจำเท่านั้น และถูก *ห่อ* (wrap) ด้วยกุญแจใน **Android Keystore**
  - ไม่ตั้ง PIN → เปิดแอปแล้วปลดล็อกอัตโนมัติผ่าน Keystore
  - ตั้ง PIN → master ถูกห่ออีกชั้นด้วย **PBKDF2-HMAC-SHA256 120,000 รอบ** ต้องใส่ PIN ทุกครั้ง
  - เปิดไบโอเมตริก → master ถูกห่อด้วย Keystore key ที่ *บังคับยืนยันตัวตน* (`setUserAuthenticationRequired`)
- **ไม่สำรองขึ้นคลาวด์** — ปิด `allowBackup` และกัน Google backup/device transfer ทั้งหมด
  ถอนแอป = ข้อมูลหายถาวร (ตั้งใจให้เป็นแบบนั้น)
- API key ของ AI อยู่ในหน่วยความจำเท่านั้น ไม่ถูกเขียนลงดิสก์ (เหมือนเดสก์ท็อป)
- แท็บรหัสผ่าน/2FA/ชื่อหน้าไม่มีการเชื่อมต่อเครือข่าย
- QR สแกนผ่าน **Google Code Scanner** จึงไม่ต้องขอสิทธิ์กล้องในแอป

> ⚠️ vault เวอร์ชันนี้ผูกกับเครื่องเดียว ยังไม่มีฟีเจอร์ export/import ข้ามเครื่อง
> ถ้าต้องการสำรอง ให้ใช้ “แสดง QR” ของแต่ละบัญชีแล้วไปสแกนเก็บในแอป Authenticator อื่น

---

## build

### ทางที่ 1 — GitHub Actions (ง่ายสุด ไม่ต้องติดตั้งอะไร)

push โค้ดขึ้น GitHub แล้วไปที่ **Actions → android → build apk**
ไฟล์ `xpass-android-debug.apk` จะอยู่ในหัวข้อ Artifacts

workflow ยังรัน unit test ของแกน TOTP (เวกเตอร์ RFC 6238) ให้ด้วย

### ทางที่ 2 — Android Studio

1. เปิดโฟลเดอร์ `android/` (ไม่ใช่โฟลเดอร์รากของ repo)
2. รอ Gradle sync (ครั้งแรกจะดาวน์โหลด dependency ประมาณ 300–500 MB)
3. กด **Run ▶** หรือ **Build → Build Bundle(s)/APK(s) → Build APK(s)**

ต้องมี **JDK 17** (Android Studio มาพร้อม JBR แล้ว)

### ทางที่ 3 — command line

```powershell
cd android
./gradlew assembleDebug          # APK สำหรับทดสอบ
./gradlew assembleRelease        # APK release (จะใช้ debug key ถ้าไม่มี keystore)
./gradlew testDebugUnitTest      # ทดสอบแกนคำนวณ
```

ไฟล์ที่ได้:

```
android/app/build/outputs/apk/debug/app-debug.apk
android/app/build/outputs/apk/release/app-release.apk
```

ติดตั้งลงมือถือ:

```powershell
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

หรือคัดลอกไฟล์ APK ไปเปิดในเครื่องแล้วอนุญาต “ติดตั้งจากแหล่งที่ไม่รู้จัก”

---

## ลงนาม release ด้วย keystore ของคุณเอง

สร้าง keystore ครั้งเดียว:

```powershell
keytool -genkeypair -v -keystore release.keystore -alias xpass `
  -keyalg RSA -keysize 4096 -validity 10000
```

แล้วตั้ง environment ก่อน build:

```powershell
$env:XPASS_KEYSTORE          = "C:\path\release.keystore"
$env:XPASS_KEYSTORE_PASSWORD = "รหัส keystore"
$env:XPASS_KEY_ALIAS         = "xpass"
$env:XPASS_KEY_PASSWORD      = "รหัส key"
./gradlew assembleRelease
```

บน GitHub ตั้ง **Secrets** 4 ตัวแทน:

| Secret | ค่า |
|---|---|
| `XPASS_KEYSTORE_BASE64` | `base64 -w0 release.keystore` |
| `XPASS_KEYSTORE_PASSWORD` | รหัส keystore |
| `XPASS_KEY_ALIAS` | `xpass` |
| `XPASS_KEY_PASSWORD` | รหัส key |

แล้ว workflow จะ build release APK ที่ลงนามแล้วให้อัตโนมัติ

---

## โครงสร้างโค้ด

```
android/app/src/main/kotlin/th/xrayth/xpass/
├── MainActivity.kt              # entry point + ล็อกอัตโนมัติเมื่อออกนาน
├── XPassViewModel.kt            # state ทั้งแอป (generator, vault, AI)
├── core/Crypto.kt               # รหัสผ่าน, base32, TOTP, otpauth, admin  ← พอร์ตจาก xpass.py
├── ai/AiClient.kt               # OpenAI + Gemini                         ← พอร์ตจาก xpass_ai.py
├── data/
│   ├── Vault.kt                 # model บัญชี TOTP + JSON
│   ├── VaultCrypto.kt           # Keystore, PBKDF2, AES-GCM
│   ├── VaultRepo.kt             # อ่าน/เขียน vault.enc, PIN, ไบโอเมตริก
│   └── SettingsRepo.kt          # ค่าตั้ง UI
├── ui/
│   ├── XPassApp.kt              # root + theme + toast
│   ├── Biometric.kt             # BiometricPrompt + CryptoObject
│   ├── theme/Theme.kt           # สีเดียวกับเดสก์ท็อป + ฟอนต์ที่แนบมา
│   ├── components/              # การ์ด, MonoText, QR dialog
│   └── screens/                 # 5 แท็บ + หน้า Lock
└── util/                        # QR สร้าง/สแกน

android/app/src/test/kotlin/.../CryptoTest.kt   # เวกเตอร์ RFC 6238
```

ไฟล์ `vault.enc` อยู่ที่ `filesDir/vault.enc` (ในเครื่อง, เข้ารหัสแล้ว)
ค่าตั้ง UI อยู่ใน `SharedPreferences("xpass_settings")`

---

## หมายเหตุ

- ฟอนต์ **IBM Plex Sans Thai** และ **JetBrains Mono** ถูกคัดลอกมาจาก `assets/fonts/`
  มาอยู่ใน `res/font/` (SIL OFL 1.1 — ดู `assets/fonts/OFL-*.txt`)
- ไบโอเมตริกต้องตั้ง PIN ก่อน เพราะถ้าไม่มี PIN แอปจะปลดล็อกอัตโนมัติผ่าน Keystore
  ทำให้การสแกนนิ้วไม่มีความหมาย
- ถ้าเครื่องไม่มี Google Play services ตัวสแกน QR จะใช้ไม่ได้ แต่ยังเพิ่มบัญชีด้วยการวาง secret ได้

### แก้ปัญหา build บน Windows ภาษาไทย

`gradle.properties` ตั้ง `-Duser.language=en -Duser.country=US` ไว้แล้ว
**อย่าลบ** — ถ้าเครื่องตั้ง locale เป็นภาษาไทย `java.util.Calendar` จะคืนปีพุทธศักราช
(เช่น 2569) ทำให้ AGP แพ็กวันที่ใน ZIP ไม่ได้ และ build ล้มด้วย:

```
com.google.common.base.VerifyException
  at com.android.tools.build.apkzlib.zip.utils.MsDosDateTimeUtils.packDate
```

ถ้ายังเจอ error นี้ ให้ตรวจว่า Gradle ใช้ `gradle.properties` ของโปรเจกต์นี้จริง
(ใน Android Studio: Settings → Build, Execution, Deployment → Gradle → Gradle JDK)
