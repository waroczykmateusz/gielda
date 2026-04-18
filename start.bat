@echo off
echo Uruchamiam backend...
start "Backend" cmd /k "cd /d C:\Users\waroc\Desktop\gielda\backend && python api.py"

timeout /t 2 /nobreak >nul

echo Uruchamiam frontend...
start "Frontend" cmd /k "cd /d C:\Users\waroc\Desktop\gielda\frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo Otwieram przegladarke...
start http://localhost:3000
