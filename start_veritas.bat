@echo off
title Veritas AI Startup
echo ==========================================
echo    Veritas AI Fact-Checker - Startup
echo ==========================================
echo.

:: Start Backend
echo [1/3] Starting Python Backend...
cd backend
start "Veritas Backend" /min cmd /c "python app.py"
cd ..

:: Start Frontend
echo [2/3] Starting Next.js Frontend...
cd ai-fact-checker-ui
start "Veritas Frontend" /min cmd /c "npm run dev"
cd ..

echo [3/3] Waiting for servers to initialize...
timeout /t 8 /nobreak > nul

echo Opening Veritas Dashboard...
start http://localhost:3000/dashboard

echo.
echo ==========================================
echo    SUCCESS: System is running!
echo    Keep this window open during use.
echo ==========================================
pause
