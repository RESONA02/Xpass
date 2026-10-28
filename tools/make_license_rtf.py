"""แปลงไฟล์ LICENSE (plain text) เป็น license.rtf สำหรับหน้า license ของ MSI"""
import os

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
text = open(os.path.join(base, "LICENSE"), encoding="utf-8").read()

out = []
for line in text.splitlines():
    safe = line.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
    if any(ord(c) > 127 for c in safe):
        safe = "".join(c if ord(c) < 128 else r"\u%d?" % ord(c) for c in safe)
    out.append(safe + r"\par")

rtf = r"{\rtf1\ansi\deff0{\fonttbl{\f0\fswiss Calibri;}}" + "\n" + r"\f0\fs20 " + "\n".join(out) + "}"
path = os.path.join(base, "installer", "license.rtf")
os.makedirs(os.path.dirname(path), exist_ok=True)
open(path, "w", encoding="ascii").write(rtf)
print("wrote", path, len(rtf), "chars")
