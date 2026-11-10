#!/bin/bash
set -e

echo "=== Starte CharAI mit integriertem Ollama ==="

mkdir -p /app/data/ollama_models
export OLLAMA_MODELS=/app/data/ollama_models

echo "-> Starte Ollama Server..."
ollama serve &

echo "-> Warte auf Ollama..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
    if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        echo "-> Ollama ist einsatzbereit!"
        break
    fi
    sleep 1
done

MODEL_NAME="${OLLAMA_MODEL:-llama3.2:1b}"
echo "-> Prüfe KI-Modell: $MODEL_NAME"
if ! ollama list 2>/dev/null | grep -q "$MODEL_NAME"; then
    echo "-> Lade Modell '$MODEL_NAME' herunter..."
    ollama pull "$MODEL_NAME" || true
fi

APP_PORT="${PORT:-7860}"
echo "-> Starte CharAI auf Port $APP_PORT..."
exec uvicorn app:app --host 0.0.0.0 --port "$APP_PORT"
