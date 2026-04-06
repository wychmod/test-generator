@echo off
chcp 65001 >nul 2>&1
python "%~dp0scripts\_do_package.py"
