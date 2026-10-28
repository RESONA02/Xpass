@echo off
rem เปิด xpass แบบ GUI (ไม่มีหน้าต่างดำ)
rem ใช้ PySide6 ถ้าติดตั้งไว้แล้ว ไม่งั้นถอยไปใช้ tkinter
cd /d "%~dp0"
python -c "import PySide6" >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw "%~dp0xpass_qt.py"
) else (
    start "" pythonw "%~dp0xpass_gui.py"
)
