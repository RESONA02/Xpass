#!/usr/bin/env python3
"""xpass_ai: ไคลเอนต์ AI ขนาดเล็กสำหรับแท็บ "ผู้ช่วย AI" ของ xpass

- รองรับ 2 ผู้ให้บริการ: OpenAI (Chat Completions) และ Google Gemini (generateContent)
- เลือกผู้ให้บริการให้อัตโนมัติจากชื่อโมเดล (ขึ้นต้นด้วย "gemini" = Google)
- ใช้ urllib จาก stdlib ล้วน จึงไม่ต้องติดตั้ง SDK เพิ่ม
- ไม่อ่าน/เขียนไฟล์ และไม่เก็บ API key ลงดิสก์
- แท็บอื่นของ xpass ยังคำนวณในเครื่องและไม่เชื่อมต่อเครือข่ายเหมือนเดิม

ตั้งค่าผ่าน environment (ทางเลือก):
  OPENAI_API_KEY     คีย์ OpenAI (ถ้าไม่ใส่ สามารถพิมพ์ในช่องของแอปได้)
  GEMINI_API_KEY     คีย์ Google AI Studio (หรือใช้ GOOGLE_API_KEY)
  OPENAI_BASE_URL    endpoint เริ่มต้น (ค่าเริ่มต้น https://api.openai.com/v1)
  GEMINI_BASE_URL    endpoint เริ่มต้น (ค่าเริ่มต้น https://generativelanguage.googleapis.com/v1beta)
  XPASS_AI_PROVIDER  ผู้ให้บริการเริ่มต้น: openai | gemini (ค่าเริ่มต้น openai)
  XPASS_AI_MODEL     ชื่อโมเดล (ถ้าไม่ใส่จะใช้ค่าเริ่มต้นของผู้ให้บริการ)
"""
from __future__ import annotations

import json
import os
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
DEFAULT_TIMEOUT = 60

PROVIDERS = ("openai", "gemini")

PROVIDER_LABELS = {
    "openai": "OpenAI",
    "gemini": "Google Gemini",
}

PROVIDER_ENV_KEYS = {
    "openai": ("OPENAI_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
}

PROVIDER_BASE_URLS = {
    "openai": DEFAULT_BASE_URL,
    "gemini": GEMINI_BASE_URL,
}

PROVIDER_BASE_URL_ENV = {
    "openai": "OPENAI_BASE_URL",
    "gemini": "GEMINI_BASE_URL",
}

PROVIDER_DEFAULT_MODELS = {
    "openai": DEFAULT_MODEL,
    "gemini": DEFAULT_GEMINI_MODEL,
}

# รายการใน drop-down ของแอป (พิมพ์ชื่อโมเดลอื่นเองได้เช่นกัน)
# หมายเหตุ: ตระกูล Gemini 2.5 ถูกจำกัดเฉพาะผู้ใช้เดิมแล้ว — ใช้รุ่น 3.x ขึ้นไป
MODEL_CHOICES = (
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite",
    "gemini-4-argon",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1-mini",
)

SYSTEM_PROMPT = (
    "คุณคือผู้ช่วยด้านความปลอดภัยของรหัสผ่านและ 2FA ภายในแอป xpass "
    "ตอบเป็นภาษาไทย กระชับ ตรงประเด็น นำไปปฏิบัติได้จริง และใช้ข้อความธรรมดา (ไม่ต้องใช้ Markdown) "
    "ห้ามขอให้ผู้ใช้ส่งรหัสผ่าน TOTP secret หรือ API key จริง "
    "ถ้าผู้ใช้ส่งข้อมูลที่ดูเหมือนความลับ ให้เตือนให้ลบทันทีและไม่ทวนซ้ำ "
    "เน้นวิธีปฏิบัติที่ทำได้ในเครื่องของผู้ใช้ และบอกข้อจำกัดอย่างตรงไปตรงมา"
)


class AIError(Exception):
    """ข้อผิดพลาดที่แสดงให้ผู้ใช้เห็นได้โดยตรง (ข้อความเป็นภาษาไทย)"""


def env_api_key(provider=None):
    """คีย์จาก environment

    ระบุ provider เพื่ออ่านคีย์ของผู้ให้บริการนั้นโดยเฉพาะ
    ถ้าไม่ระบุ จะคืนคีย์ตัวแรกที่พบ (OpenAI ก่อน แล้วจึง Gemini)
    """
    if provider in PROVIDER_ENV_KEYS:
        for name in PROVIDER_ENV_KEYS[provider]:
            value = os.environ.get(name, "").strip()
            if value:
                return value
        return ""
    for name in PROVIDERS:
        value = env_api_key(name)
        if value:
            return value
    return ""


def env_key_name(provider):
    """ชื่อ environment variable ที่มีคีย์อยู่ ('' ถ้าไม่มี)"""
    for name in PROVIDER_ENV_KEYS.get(provider, ()):
        if os.environ.get(name, "").strip():
            return name
    return ""


def default_provider():
    """ผู้ให้บริการเริ่มต้นจาก XPASS_AI_PROVIDER (openai ถ้าไม่ตั้งหรือค่าไม่ถูกต้อง)"""
    value = os.environ.get("XPASS_AI_PROVIDER", "").strip().lower()
    return value if value in PROVIDERS else "openai"


def provider_for_model(model):
    """เดาผู้ให้บริการจากชื่อโมเดล — ขึ้นต้นด้วย gemini = Google"""
    name = (model or "").strip().lower()
    if name.startswith("gemini") or name.startswith("models/gemini"):
        return "gemini"
    return default_provider()


def provider_label(provider):
    return PROVIDER_LABELS.get(provider, provider or "")


def base_url(provider="openai"):
    """endpoint เริ่มต้น เช่น https://api.openai.com/v1"""
    env_name = PROVIDER_BASE_URL_ENV.get(provider, "")
    value = os.environ.get(env_name, "").strip() if env_name else ""
    return (value or PROVIDER_BASE_URLS.get(provider, DEFAULT_BASE_URL)).rstrip("/")


def default_model(provider=None):
    """โมเดลเริ่มต้น — XPASS_AI_MODEL มาก่อนเสมอ"""
    env_model = os.environ.get("XPASS_AI_MODEL", "").strip()
    if env_model:
        return env_model
    if provider not in PROVIDERS:
        provider = default_provider()
    return PROVIDER_DEFAULT_MODELS.get(provider, DEFAULT_MODEL)


def _http_detail(exc):
    """ดึงข้อความ error จาก body ของ HTTPError แบบไม่ให้ยาวเกินไป"""
    try:
        raw = exc.read().decode("utf-8", "replace")
    except Exception:
        return ""
    try:
        obj = json.loads(raw)
        err = obj.get("error") if isinstance(obj, dict) else None
        msg = err.get("message") if isinstance(err, dict) else obj.get("message") if isinstance(obj, dict) else None
        return str(msg or raw).strip()[:300]
    except Exception:
        return raw.strip()[:300]


def _suggested_model(detail, current):
    """ดึงชื่อโมเดลที่เซิร์ฟเวอร์แนะนำจากข้อความ error (ถ้ามี)"""
    current = (current or "").strip()
    if current.startswith("models/"):
        current = current[len("models/"):]
    for name in re.findall(r"models/([A-Za-z0-9][A-Za-z0-9._-]*)", detail or ""):
        if name != current:
            return name
    return ""


def _http_message(exc, provider, model):
    """ข้อความภาษาไทยสำหรับ HTTPError (บอกผู้ให้บริการและชื่อโมเดล)"""
    label = provider_label(provider)
    hints = {
        400: "%s: คำขอไม่ถูกต้อง — อาจเป็นชื่อโมเดล รูปแบบข้อความ หรือ API key (400)" % label,
        401: "API key ไม่ถูกต้องหรือถูกยกเลิกแล้ว (401)",
        403: "คีย์นี้ไม่มีสิทธิ์ใช้โมเดลที่เลือก (403)",
        404: "%s: ไม่พบ endpoint หรือโมเดลที่เลือก (404)" % label,
        429: "ติด rate limit หรือโควตาหมด — ลองใหม่ภายหลัง (429)",
        500: "%s ขัดข้อง — ลองใหม่ภายหลัง (500)" % label,
        502: "%s ขัดข้อง — ลองใหม่ภายหลัง (502)" % label,
        503: "%s ไม่พร้อมให้บริการ — ลองใหม่ภายหลัง (503)" % label,
    }
    message = hints.get(exc.code, "%s ตอบกลับ HTTP %d" % (label, exc.code))
    detail = _http_detail(exc)
    if exc.code == 404:
        message += " — ตรวจชื่อโมเดล “%s”" % model
        if provider == "gemini":
            suggestion = _suggested_model(detail, model)
            if suggestion:
                message += " — แนะนำ “%s”" % suggestion
            message += " (โมเดลรุ่นเก่าอาจถูกปิดสำหรับผู้ใช้ใหม่ — กด “รีเฟรช” เพื่อดูรุ่นที่คีย์นี้ใช้ได้)"
    if detail:
        message += ": " + detail
    return message


def _request_json(url, headers, provider, model, timeout, payload=None):
    """เรียก HTTP แล้วคืน dict ที่ parse แล้ว (payload=None = GET, แปลง error เป็น AIError)"""
    all_headers = {"User-Agent": "xpass/1.2"}
    if payload is not None:
        all_headers["Content-Type"] = "application/json; charset=utf-8"
    all_headers.update(headers)
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None,
        method="POST" if payload is not None else "GET",
        headers=all_headers,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raise AIError(_http_message(exc, provider, model)) from None
    except (TimeoutError, socket.timeout):
        raise AIError("หมดเวลาเชื่อมต่อ (%d วินาที) — ตรวจอินเทอร์เน็ตแล้วลองใหม่" % timeout) from None
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise AIError("เชื่อมต่ออินเทอร์เน็ตไม่ได้: %s" % reason) from None

    try:
        data = json.loads(body)
    except ValueError:
        raise AIError("อ่านคำตอบจากเซิร์ฟเวอร์ไม่ได้ (ไม่ใช่ JSON)") from None
    if not isinstance(data, dict):
        raise AIError("คำตอบจากเซิร์ฟเวอร์ไม่ถูก formato")
    return data


def _post_json(url, payload, headers, provider, model, timeout):
    """POST JSON แล้วคืน dict ที่ parse แล้ว"""
    return _request_json(url, headers, provider, model, timeout, payload=payload)


def _chat_openai(messages, api_key, model, temperature, timeout):
    payload = {"model": model, "messages": messages, "temperature": temperature}
    data = _post_json(
        base_url("openai") + "/chat/completions",
        payload,
        {"Authorization": "Bearer " + api_key},
        "openai",
        model,
        timeout,
    )

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise AIError("คำตอบจากเซิร์ฟเวอร์ไม่ถูก formato") from None

    if isinstance(content, list):  # รองรับ content แบบเป็นชิ้น ๆ
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text") or part.get("content") or "")
        content = "".join(parts)

    return (content or "").strip()


def _gemini_payload(messages, temperature):
    """แปลงบทสนทนาแบบ OpenAI ให้เป็นรูปแบบ contents ของ Gemini"""
    contents = []
    system_parts = []
    for msg in messages:
        role = msg["role"]
        if role == "system":
            system_parts.append(msg["content"])
            continue
        contents.append({
            "role": "model" if role == "assistant" else "user",
            "parts": [{"text": msg["content"]}],
        })

    payload = {"contents": contents, "generationConfig": {"temperature": temperature}}
    system = "\n\n".join(part for part in system_parts if part)
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    return payload


def _chat_gemini(messages, api_key, model, temperature, timeout):
    name = model[len("models/"):] if model.startswith("models/") else model
    url = "%s/models/%s:generateContent" % (
        base_url("gemini"),
        urllib.parse.quote(name, safe=""),
    )
    data = _post_json(
        url,
        _gemini_payload(messages, temperature),
        {"x-goog-api-key": api_key},
        "gemini",
        model,
        timeout,
    )

    candidates = data.get("candidates") or []
    feedback = data.get("promptFeedback") or {}
    if not candidates:
        blocked = feedback.get("blockReason")
        if blocked:
            raise AIError("Gemini ปฏิเสธคำขอนี้ด้วยตัวกรองความปลอดภัย (%s)" % blocked)
        err = data.get("error") or {}
        detail = str(err.get("message") or "").strip()
        raise AIError("Gemini ไม่ได้ส่งคำตอบกลับมา" + (": " + detail if detail else ""))

    candidate = candidates[0] or {}
    parts = (candidate.get("content") or {}).get("parts") or []
    text = "".join(
        part.get("text", "") for part in parts if isinstance(part, dict)
    ).strip()
    if not text:
        reason = str(candidate.get("finishReason") or "").strip()
        if reason and reason != "STOP":
            raise AIError("Gemini หยุดตอบกลางทาง (%s) — ลองถามใหม่หรือเปลี่ยนโมเดล" % reason)
    return text


_GEMINI_SKIP = (
    "image", "tts", "live", "transcribe", "embedding", "robotics",
    "computer-use", "deep-research", "nano-banana", "omni", "veo", "lyria",
)

_OPENAI_SKIP = (
    "embedding", "tts", "whisper", "dall-e", "moderation", "audio",
    "realtime", "transcribe", "image", "search",
)


def _gemini_model_ok(name):
    low = name.lower()
    return low.startswith("gemini") and not any(word in low for word in _GEMINI_SKIP)


def _openai_model_ok(name):
    low = name.lower()
    if any(word in low for word in _OPENAI_SKIP):
        return False
    return low.startswith(("gpt-", "chatgpt", "o1", "o3", "o4"))


def _model_sort_key(name):
    """เรียงรุ่นใหม่ก่อน เช่น gemini-4-argon > gemini-3.8-flash > gemini-3.6-flash"""
    return [int(part) for part in re.findall(r"\d+", name.lower())[:3]]


def list_models(key=None, provider=None, timeout=DEFAULT_TIMEOUT):
    """ดึงรายชื่อโมเดลที่ API key นี้เรียกใช้ได้ (สำหรับเติม drop-down)

    คืน list ของชื่อโมเดล เรียงรุ่นใหม่ก่อน
    """
    provider = (provider or "").strip().lower() if isinstance(provider, str) else ""
    if provider not in PROVIDERS:
        provider = default_provider()

    api_key = (key or env_api_key(provider)).strip()
    if not api_key:
        raise AIError("ยังไม่มี API key ของ %s — ใส่คีย์ก่อนดึงรายการโมเดล หรือตั้งค่า %s"
                      % (provider_label(provider), " หรือ ".join(PROVIDER_ENV_KEYS[provider])))

    models = []
    if provider == "gemini":
        page_token = ""
        for _ in range(10):  # กันวนไม่จบถ้าเซิร์ฟเวอร์ส่ง token ซ้ำ
            query = "?pageSize=1000"
            if page_token:
                query += "&pageToken=" + urllib.parse.quote(page_token, safe="")
            data = _request_json(
                base_url("gemini") + "/models" + query,
                {"x-goog-api-key": api_key},
                provider, "", timeout,
            )
            for item in data.get("models") or []:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or "")
                if name.startswith("models/"):
                    name = name[len("models/"):]
                methods = item.get("supportedGenerationMethods") or []
                if name and "generateContent" in methods and _gemini_model_ok(name):
                    models.append(name)
            page_token = str(data.get("nextPageToken") or "")
            if not page_token:
                break
    else:
        data = _request_json(
            base_url("openai") + "/models",
            {"Authorization": "Bearer " + api_key},
            provider, "", timeout,
        )
        for item in data.get("data") or []:
            if isinstance(item, dict) and item.get("id"):
                name = str(item["id"])
                if _openai_model_ok(name):
                    models.append(name)

    seen = set()
    unique = []
    for name in models:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    return sorted(unique, key=_model_sort_key, reverse=True)


def chat(messages, key=None, model=None, provider=None, temperature=0.7, timeout=DEFAULT_TIMEOUT):
    """ส่งบทสนทนาไปยังผู้ให้บริการ AI และคืนข้อความตอบกลับ

    messages: list ของ {"role": "system"|"user"|"assistant", "content": str}
    key:      API key (ถ้าไม่ใส่จะอ่านจาก OPENAI_API_KEY / GEMINI_API_KEY)
    model:    ชื่อโมเดล เช่น "gemini-2.5-flash" หรือ "gpt-4o-mini"
    provider: "openai" | "gemini" (ถ้าไม่ใส่จะเดาจากชื่อโมเดล)
    """
    model = (model or "").strip() or default_model(provider)
    provider = (provider or "").strip().lower() if isinstance(provider, str) else ""
    if provider not in PROVIDERS:
        provider = provider_for_model(model)

    api_key = (key or env_api_key(provider)).strip()
    if not api_key:
        raise AIError(
            "ยังไม่มี API key ของ %s — ตั้งค่า %s หรือใส่คีย์ในช่องด้านบน"
            % (provider_label(provider), " หรือ ".join(PROVIDER_ENV_KEYS[provider]))
        )

    if not isinstance(messages, (list, tuple)) or not messages:
        raise AIError("ยังไม่มีข้อความที่จะส่ง")
    clean = []
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") and isinstance(msg.get("content"), str):
            clean.append({"role": msg["role"], "content": msg["content"]})
    if not clean:
        raise AIError("รูปแบบข้อความไม่ถูกต้อง")

    try:
        temperature = max(0.0, min(2.0, float(temperature)))
    except (TypeError, ValueError):
        temperature = 0.7

    if provider == "gemini":
        content = _chat_gemini(clean, api_key, model, temperature, timeout)
    else:
        content = _chat_openai(clean, api_key, model, temperature, timeout)

    if not content:
        raise AIError("AI ไม่ได้ส่งคำตอบกลับมา — ลองใหม่อีกครั้ง")
    return content
