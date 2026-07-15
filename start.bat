@echo off
cd /d "%~dp0"

echo ========================================
echo  AeroClub - Iniciando servidores
echo ========================================

echo.
echo Parando processos anteriores...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /f /pid %%a 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [1/2] Iniciando backend em http://localhost:8000
cd backend
start "AeroClub-Backend" cmd /c python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd ..

echo [2/2] Iniciando frontend em http://localhost:3000
cd frontend
start "AeroClub-Frontend" cmd /c npm run dev

echo.
echo ========================================
echo  Servidores iniciados!
echo  Backend: http://localhost:8000
echo  Frontend: http://localhost:3000
echo  Feche este terminal para parar tudo.
echo ========================================

pause
