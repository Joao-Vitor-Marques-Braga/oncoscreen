@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   OncoScreen.AI (OralCare-Vision CDSS) - Inicializacao Nativa
echo ============================================================

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [INFO] Arquivo .env criado a partir de .env.example
    )
)

echo [1/4] Verificando ambiente Python do Backend...
cd backend
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo [2/4] Iniciando Backend FastAPI (http://127.0.0.1:8000)...
start "OncoScreen Backend" cmd /k "cd /d %CD% && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

cd ..\frontend
echo [3/4] Verificando dependencias Node.js do Frontend...
if not exist "node_modules" (
    call npm install
)

echo [4/4] Iniciando Frontend Vite (http://localhost:5173)...
start "OncoScreen Frontend" cmd /k "cd /d %CD% && npm run dev"

echo.
echo [OK] Servicos iniciados! Acesse: http://localhost:5173
echo Credencial inicial Medico: doutor@oncoscreen.ai / admin123
pause

