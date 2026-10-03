@echo off
cd /d "%~dp0backend"
echo Starting MediSync Backend...
.\venv\Scripts\python.exe run.py
