@echo off
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\PAARTH DUTTA\Downloads\whatsapp bot fronend\backend"
"C:\Users\PAARTH DUTTA\Downloads\whatsapp bot fronend\backend\venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
