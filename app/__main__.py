"""Запуск: python -m app  (порт берётся из переменной окружения PORT, по умолчанию 8000)."""
import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")))
