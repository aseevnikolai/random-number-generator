# Генератор случайных чисел

Небольшое веб-приложение на Python (FastAPI): генерирует случайное число в заданном диапазоне
и сохраняет историю в базе данных PostgreSQL.

## Возможности

- веб-страница: диапазон «от – до», кнопка «Сгенерировать», история последних чисел;
- REST API: `POST /api/numbers?min=1&max=100`, `GET /api/numbers`, `GET /api/info`;
- проверка работоспособности: `GET /health` (приложение отвечает, база доступна);
- документация API: `/docs`.

## Настройки (переменные окружения)

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `PORT` | `8000` | порт веб-сервера |
| `APP_TITLE` | Генератор случайных чисел | заголовок страницы |
| `APP_ENV` | `local` | метка окружения |
| `DEFAULT_MIN`, `DEFAULT_MAX` | `1`, `100` | диапазон по умолчанию |
| `HISTORY_LIMIT` | `10` | сколько чисел показывать в истории |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` | `localhost`, `5432`, `rng`, `rng` | подключение к PostgreSQL |
| `DB_PASSWORD` | — | пароль к PostgreSQL (обязателен) |

Данные хранятся в таблице `numbers`; приложение создаёт её само при запуске.

## Локальный запуск

Нужны Python 3.12+ и доступный сервер PostgreSQL.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
DB_HOST=localhost DB_PORT=5432 DB_NAME=rng DB_USER=rng DB_PASSWORD=<пароль> .venv/bin/python -m app
# приложение: http://localhost:8000
```
