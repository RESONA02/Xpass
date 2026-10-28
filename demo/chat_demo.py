#!/usr/bin/env python3
"""chat_demo: ตัวอย่างเรียก OpenAI Chat Completions ด้วย openai SDK

ไว้ทดลองว่าคีย์ OpenAI ใช้งานได้หรือไม่
- อ่านคีย์จาก environment (OPENAI_API_KEY / GEMINI_API_KEY) เป็นหลัก
- ถ้าอยากเก็บคีย์ในไฟล์ ให้สร้าง demo/api_key.txt เอง (มีกฎใน .gitignore กันไว้แล้ว)
  แต่ไม่ควร commit ไฟล์นั้น — ใช้ env ปลอดภัยกว่า
- ไม่ยุ่งกับฟังก์ชันของ xpass — เป็นไฟล์ตัวอย่างแยกต่างหาก ลบทิ้งได้

ตัวอย่าง:
  $env:OPENAI_API_KEY = "sk-..."               # แนะนำ
  python demo\\chat_demo.py                    # ใช้คีย์จาก env (หรือ demo\\api_key.txt ถ้ามี)
  python demo\\chat_demo.py "ช่วยอธิบาย TOTP ให้เข้าใจง่าย ๆ"
  python demo\\chat_demo.py --stream

ใช้ผู้ให้บริการอื่นที่เข้ากันได้กับ OpenAI (ฟรีก็มี):
  python demo\\chat_demo.py --base-url https://api.groq.com/openai/v1 --model openai/gpt-oss-120b
  python demo\\chat_demo.py --base-url http://localhost:11434/v1 --model llama3.2   # Ollama ในเครื่อง
"""
from __future__ import annotations

import argparse
import os
import re
import sys

DEFAULT_MODEL = os.environ.get("XPASS_AI_MODEL", "").strip() or "gpt-4o-mini"
SYSTEM_PROMPT = (
    "คุณคือผู้ช่วยอัจฉริยะที่คอยให้คำแนะนำที่เป็นประโยชน์ "
    "ตอบเป็นภาษาไทย กระชับ ตรงประเด็น นำไปปฏิบัติได้จริง"
)

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")


def key_from_file(path=KEY_FILE):
    """คีย์จากไฟล์ — ใช้บรรทัดแรกที่ไม่ใช่คอมเมนต์/บรรทัดว่าง (คืน "" ถ้าไม่มี)"""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line
    except OSError:
        pass
    return ""


def load_api_key():
    """คีย์จาก env ก่อน ( OPENAI_API_KEY หรือ GEMINI_API_KEY ) ถ้าไม่มีจึงอ่านไฟล์ — คืน (คีย์, แหล่งที่มา)"""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key, "environment (OPENAI_API_KEY)"
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key, "environment (GEMINI_API_KEY)"
    return key_from_file(), KEY_FILE


KEY_PATTERN = re.compile(r"^(sk-|AIza)[A-Za-z0-9_\-\.]{20,}$")


def looks_like_key(key):
    """คีย์จริงต้องขึ้นต้นด้วย sk- และยาวพอ (กันค่าว่าง/ค่าตัวอย่าง)"""
    return bool(KEY_PATTERN.match(key or ""))


def main(argv=None):
    parser = argparse.ArgumentParser(description="ทดลองเรียก OpenAI Chat Completions")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="สวัสดี! ช่วยแนะนำวิธีดูแลสุขภาพเบื้องต้นหน่อย",
        help="ข้อความที่ต้องการถาม",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="ชื่อโมเดล (ค่าเริ่มต้น gpt-4o-mini)")
    parser.add_argument("--temperature", type=float, default=0.7, help="0 = นิ่ง, 1 = สร้างสรรค์")
    parser.add_argument("--stream", action="store_true", help="พิมพ์คำตอบทีละคำ")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL", "").strip(),
        help="endpoint ที่เข้ากันได้กับ OpenAI เช่น https://api.groq.com/openai/v1 "
        "หรือ http://localhost:11434/v1 (ว่าง = ใช้ api.openai.com)",
    )
    args = parser.parse_args(argv)

    base = (args.base_url or "").strip().rstrip("/")
    local = any(h in base for h in ("localhost", "127.0.0.1", "[::1]"))

    key, source = load_api_key()
    if local and not key:
        key = "ollama"  # Ollama ไม่ตรวจคีย์ แต่ SDK บังคับให้มีค่า
    usable = looks_like_key(key) or (bool(base) and len(key) >= 10) or key.startswith("AIza")
    if not usable:
        print("ยังไม่มี API key ที่ใช้ได้ — ใส่ได้ตามนี้:")
        print("  1) แก้ไฟล์นี้ ให้บรรทัดคีย์เป็นคีย์จริง (OpenAI sk-... หรือ Gemini AIza...):")
        print("     %s" % KEY_FILE)
        print('  2) ตั้ง environment: $env:OPENAI_API_KEY = "sk-..." หรือ $env:GEMINI_API_KEY = "AIza..."')
        print("  (ถ้าใช้ Gemini ผ่าน OpenAI Compatible ให้ใส่ --base-url https://generativelanguage.googleapis.com/v1beta/openai/)")
        return 2

    try:
        import openai
        from openai import OpenAI
    except ImportError:
        print("ยังไม่ได้ติดตั้ง openai SDK — รัน: pip install openai")
        return 2

    client = OpenAI(api_key=key, base_url=base or None)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": args.prompt},
    ]

    try:
        if args.stream:
            stream = client.chat.completions.create(
                model=args.model,
                messages=messages,
                temperature=args.temperature,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    print(delta, end="", flush=True)
            print()
            return 0

        resp = client.chat.completions.create(
            model=args.model,
            messages=messages,
            temperature=args.temperature,
        )
        print(resp.choices[0].message.content or "")
        usage = getattr(resp, "usage", None)
        if usage is not None:
            print("\n--- โทเคน: เข้า %s / ออก %s ---" % (usage.prompt_tokens, usage.completion_tokens))
        return 0

    except openai.AuthenticationError:
        print("401 — คีย์ไม่ถูกต้อง ถูกยกเลิก หรือมีช่องว่างติดมา")
    except openai.RateLimitError as exc:
        code = getattr(exc, "code", None)
        kind = getattr(exc, "type", None)
        if kind == "insufficient_quota" or code in ("insufficient_quota", "credit_balance_exhausted"):
            print("429 — เครดิต API หมด ต้องเติมเงินที่ Billing ก่อน (API แยกจาก ChatGPT Plus)")
        else:
            print("429 — ยิงถี่เกินโควตา ลองรอสักครู่")
    except openai.NotFoundError:
        print("404 — ไม่พบโมเดล '%s' หรือบัญชีไม่มีสิทธิ์ใช้" % args.model)
    except openai.APIConnectionError:
        print("เชื่อมต่อ %s ไม่ได้ — ตรวจอินเทอร์เน็ต/พร็อกซี่/เซิร์ฟเวอร์" % (base or "api.openai.com"))
    except openai.APIStatusError as exc:
        print("OpenAI ตอบกลับ HTTP %s: %s" % (exc.status_code, exc.message))
    return 1


if __name__ == "__main__":
    sys.exit(main())
