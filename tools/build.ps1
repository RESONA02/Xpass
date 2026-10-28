# สร้าง xpass.exe และตัวติดตั้ง .msi
# ใช้: powershell -ExecutionPolicy Bypass -File tools\build.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "[1/4] สร้างไอคอน"
python tools\make_icon.py

Write-Host "[2/4] build exe ด้วย PyInstaller"
$fontData = "assets\fonts" + [IO.Path]::PathSeparator + "assets\fonts"
python -m PyInstaller --noconfirm --clean --windowed --onedir --name xpass `
    --icon "tools\assets\xpass.ico" --add-data $fontData xpass_qt.py

Write-Host "[3/4] สร้างรายการไฟล์สำหรับ MSI"
if (-not (Test-Path "tools\wix\candle.exe")) {
    throw "ไม่พบ WiX ใน tools\wix — ดาวน์โหลด wix314-binaries.zip แล้วแตกไว้ในโฟลเดอร์นั้น"
}
python tools\make_license_rtf.py
& .\tools\wix\heat.exe dir "dist\xpass" -cg AppFiles -dr INSTALLFOLDER -gg -g1 -srd -sreg -sfrag -var var.SourceDir -out "tools\files.wxs"
New-Item -ItemType Directory -Force -Path "build\wix" | Out-Null

Write-Host "[4/4] คอมไพล์ MSI"
& .\tools\wix\candle.exe -nologo -arch x64 -dSourceDir="dist\xpass" -out "build\wix\" installer\Product.wxs tools\files.wxs
& .\tools\wix\light.exe -nologo -ext WixUIExtension -cultures:en-us -out "installer\xpass-1.0.1.msi" "build\wix\Product.wixobj" "build\wix\files.wixobj"

Write-Host ""
Write-Host "เสร็จแล้ว:" -ForegroundColor Green
Write-Host "  แอปพกพา : dist\xpass\xpass.exe"
Write-Host "  ตัวติดตั้ง: installer\xpass-1.0.1.msi"
