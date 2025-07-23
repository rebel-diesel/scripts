@echo off
setlocal

REM Вызываем PowerShell-скрипт
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0draw_tree.ps1" "%cd%"