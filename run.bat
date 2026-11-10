@echo off
title CharAI Local - Character.ai Clone
echo ========================================================
echo         CharAI Local - Character.ai Klon
echo ========================================================
echo.
:: Prüfe und starte Ollama im Hintergrund, falls nicht aktiv
powershell -Command "if (!(Get-Process ollama* -ErrorAction SilentlyContinue)) { if (Test-Path 'C:\Users\EpicS\AppData\Local\Programs\Ollama\ollama app.exe') { Start-Process 'C:\Users\EpicS\AppData\Local\Programs\Ollama\ollama app.exe' } }"

echo Starte Web-Server auf http://127.0.0.1:8000 ...
echo Dein Standard-Browser wird in wenigen Sekunden geoeffnet.
echo Zum Beenden einfach dieses Fenster schliessen oder Strg+C druecken.
echo.

python app.py
pause
