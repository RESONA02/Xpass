#!/usr/bin/env python3
"""xpass: สร้างรหัสผ่าน / secret 2FA (TOTP) / ชื่อหน้าลับ แบบออฟไลน์ล้วน
ใช้แค่ไลบรารีมาตรฐานของ Python (ไม่ต้องติดตั้งอะไร) ไม่ต่อเน็ต ไม่เขียนไฟล์ ไม่เก็บอะไรไว้
QR code เป็นตัวเลือก: ถ้าติดตั้ง `pip install qrcode` ไว้ จะพิมพ์ QR ให้ด้วย
ใช้ได้ทั้ง Windows / macOS / Linux / Android (Termux)
"""
import argparse
import base64
import getpass
import hashlib
import hmac
import math
import os
import secrets
import string
import struct
import sys
import time
from urllib.parse import quote

LOWER, UPPER, DIGITS = string.ascii_lowercase, string.ascii_uppercase, string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{}:,.?"
AMBIG = "Il1O0o"


# ---------- รหัสผ่าน / ชื่อสุ่ม (ใช้ secrets = ตัวสุ่มของระบบปฏิบัติการ) ----------
def gen_password(length=20, symbols=True, no_ambig=False):
    classes = [LOWER, UPPER, DIGITS] + ([SYMBOLS] if symbols else [])
    if no_ambig:
        classes = ["".join(c for c in k if c not in AMBIG) for k in classes]
    pool = "".join(classes)
    while True:
        s = "".join(secrets.choice(pool) for _ in range(length))
        if all(any(ch in k for ch in s) for k in classes):
            return s, length * math.log2(len(pool))


def gen_alnum(n):
    pool = LOWER + UPPER + DIGITS
    return "".join(secrets.choice(pool) for _ in range(n))


def gen_slug(n=24):
    pool = LOWER + DIGITS
    return "".join(secrets.choice(pool) for _ in range(n))


# ---------- TOTP (SHA-1, 6 หลัก, 30 วินาที ตรงกับ admin worker และแอป Authenticator) ----------
def b32enc(raw: bytes) -> str:
    return base64.b32encode(raw).decode().rstrip("=")


def b32dec(text: str) -> bytes:
    t = "".join(text.split()).replace("-", "").rstrip("=").upper()
    return base64.b32decode(t + "=" * (-len(t) % 8))


def totp(key: bytes, step: int, digits: int = 6) -> str:
    mac = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
    o = mac[19] & 15
    n = struct.unpack(">I", mac[o:o + 4])[0] & 0x7FFFFFFF
    return str(n % 10 ** digits).zfill(digits)


def otpauth_uri(secret, issuer, account):
    return ("otpauth://totp/%s:%s?secret=%s&issuer=%s&algorithm=SHA1&digits=6&period=30"
            % (quote(issuer, safe=""), quote(account, safe=""), secret, quote(issuer, safe="")))


def read_secret() -> bytes:
    s = os.environ.get("XPASS_SECRET", "").strip() or getpass.getpass("ใส่ secret (base32, ไม่แสดงตัวอักษร): ")
    try:
        k = b32dec(s)
        if not k:
            raise ValueError
        return k
    except Exception:
        sys.exit("secret ไม่ถูกต้อง (ต้องเป็นตัวอักษร A-Z กับเลข 2-7)")


def print_qr(data, light=False):
    try:
        import qrcode
    except ImportError:
        print("(ไม่มี QR: ติดตั้งด้วย `pip install qrcode` หรือใส่ secret เองในแอป)")
        return
    q = qrcode.QRCode(border=1)
    q.add_data(data)
    q.make()
    q.print_ascii(invert=not light)  # ค่าเริ่มต้นเหมาะกับเทอร์มินัลพื้นหลังเข้ม; ใช้ --light ถ้าพื้นหลังสว่าง


# ---------- คำสั่ง ----------
def cmd_pw(a):
    if not 8 <= a.length <= 128:
        sys.exit("ความยาวต้องอยู่ระหว่าง 8–128")
    bits = 0
    for _ in range(max(1, min(a.n, 50))):
        p, bits = gen_password(a.length, not a.s, a.a)
        print(p)
    print("(ประมาณ %d บิต entropy)" % bits, file=sys.stderr)


def cmd_name(a):
    n = max(8, min(a.length, 64))
    print("%s%s.html" % (a.prefix, gen_slug(n)))
    print("(ประมาณ %d บิต entropy)" % (n * math.log2(36)), file=sys.stderr)


def cmd_admin(a):
    token = gen_alnum(40)
    secret = b32enc(secrets.token_bytes(20))  # 160 บิต
    page = "a-%s.html" % gen_slug(24)
    uri = otpauth_uri(secret, a.issuer, a.account)
    code = totp(b32dec(secret), int(time.time()) // 30)
    print("=== ค่าสำหรับ admin worker (แสดงครั้งเดียว ไม่ถูกบันทึกที่ไหน) ===\n")
    print("ADMIN_TOKEN        =", token)
    print("ADMIN_TOTP_SECRET  =", secret)
    print("ชื่อหน้า admin ลับ   =", page, "\n")
    print("--- ตั้งค่าใน Cloudflare ---")
    print("wrangler secret put ADMIN_TOKEN        # วาง token ด้านบน")
    print("wrangler secret put ADMIN_TOTP_SECRET  # วาง secret ด้านบน\n")
    print("--- เพิ่มเข้าแอป Authenticator ---")
    if not a.no_qr:
        print("สแกน QR ด้านล่างด้วยแอปบนมือถือ (ล้างจอหลังสแกน)\n")
        print_qr(uri, a.light)
    print("หรือ: แอป → เพิ่มบัญชี → ใส่คีย์เอง → วาง ADMIN_TOTP_SECRET (time-based)")
    print("ลิงก์ otpauth:", uri, "\n")
    print("รหัสตอนนี้ที่ควรตรงกับแอป: %s %s" % (code[:3], code[3:]))
    print("(ถ้าตรง แปลว่าตั้งค่าถูก; ใช้ `xpass.py verify <รหัส>` เช็กภายหลังได้)")


def cmd_totp(a):
    key = read_secret()
    try:
        while True:
            now = int(time.time())
            code = totp(key, now // 30)
            print("\r🔑 %s %s   (เปลี่ยนใน %2d วิ)  " % (code[:3], code[3:], 30 - now % 30), end="", flush=True)
            if a.once:
                print()
                return
            time.sleep(1)
    except KeyboardInterrupt:
        print()


def cmd_verify(a):
    key = read_secret()
    code = "".join(a.code.split())
    step = int(time.time()) // 30
    for d in (0, -1, 1):
        if hmac.compare_digest(totp(key, step + d), code):
            print("✅ รหัสถูกต้อง (คลาดเวลา %d ช่วง)" % d)
            return
    print("❌ รหัสไม่ตรง (เช็กเวลาเครื่อง/secret)")
    sys.exit(1)


def cmd_selftest(_a):
    k = b"12345678901234567890"
    vec = {59: "287082", 1111111109: "081804", 1111111111: "050471", 1234567890: "005924", 2000000000: "279037"}
    for t, want in vec.items():
        assert totp(k, t // 30) == want, (t, totp(k, t // 30), want)
    assert b32enc(b"foobar") == "MZXW6YTBOI" and b32dec("MZXW6YTBOI======") == b"foobar"
    p, _ = gen_password(16, True, True)
    assert any(c in LOWER for c in p) and any(c in UPPER for c in p) and any(c in DIGITS for c in p)
    assert any(c in SYMBOLS for c in p) and not any(c in AMBIG for c in p)
    print("✅ selftest ผ่านทั้งหมด (TOTP ตรงกับ RFC 6238)")


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # ให้ cmd/PowerShell แสดงภาษาไทยได้ (ทั้ง stdout และ stderr)
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="xpass.py", description="เครื่องมือรหัสผ่าน/2FA/ชื่อลับ แบบออฟไลน์")
    sp = ap.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("pw", help="สร้างรหัสผ่าน")
    s.add_argument("length", nargs="?", type=int, default=20)
    s.add_argument("-n", type=int, default=1, help="จำนวนชุด")
    s.add_argument("-s", action="store_true", help="ไม่ใส่สัญลักษณ์")
    s.add_argument("-a", action="store_true", help="ตัดตัวที่สับสน Il1O0o")
    s.set_defaults(f=cmd_pw)

    s = sp.add_parser("name", help="ชื่อไฟล์/URL ลับแบบสุ่ม")
    s.add_argument("length", nargs="?", type=int, default=24)
    s.add_argument("prefix", nargs="?", default="a-")
    s.set_defaults(f=cmd_name)

    s = sp.add_parser("admin", help="สร้าง ADMIN_TOKEN + TOTP secret + ชื่อหน้าลับ")
    s.add_argument("--issuer", default="XRay Admin")
    s.add_argument("--account", default="admin")
    s.add_argument("--no-qr", action="store_true")
    s.add_argument("--light", action="store_true", help="QR สำหรับเทอร์มินัลพื้นหลังสว่าง")
    s.set_defaults(f=cmd_admin)

    s = sp.add_parser("totp", help="แสดงรหัส 6 หลักสด (authenticator ออฟไลน์)")
    s.add_argument("--once", action="store_true")
    s.set_defaults(f=cmd_totp)

    s = sp.add_parser("verify", help="ตรวจรหัส TOTP (±1 ช่วง)")
    s.add_argument("code")
    s.set_defaults(f=cmd_verify)

    s = sp.add_parser("selftest", help="ทดสอบตัวเอง")
    s.set_defaults(f=cmd_selftest)

    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
