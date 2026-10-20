"""Генератор случайных чисел с историей в PostgreSQL."""
import html
import os
import random
import socket
import time
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

from app import __version__

# Настройки берутся из переменных окружения
APP_TITLE = os.getenv("APP_TITLE", "Генератор случайных чисел")
APP_ENV = os.getenv("APP_ENV", "local")
DEFAULT_MIN = int(os.getenv("DEFAULT_MIN", "1"))
DEFAULT_MAX = int(os.getenv("DEFAULT_MAX", "100"))
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "10"))
INSTANCE = socket.gethostname()

DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "rng"),
    "user": os.getenv("DB_USER", "rng"),
    "password": os.getenv("DB_PASSWORD", ""),
    "connect_timeout": 5,
}


def connect():
    return psycopg.connect(**DB, autocommit=True)


def init_db(attempts=30):
    """Создаёт таблицу; ждёт, пока база станет доступна."""
    if not DB["password"]:
        raise SystemExit("ОШИБКА: не задана переменная окружения DB_PASSWORD")
    for attempt in range(1, attempts + 1):
        try:
            with connect() as conn, conn.transaction():
                # Несколько реплик могут стартовать одновременно: без блокировки параллельные
                # CREATE TABLE IF NOT EXISTS конфликтуют в системном каталоге PostgreSQL.
                conn.execute("SELECT pg_advisory_xact_lock(20261020)")
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS numbers (
                           id         SERIAL PRIMARY KEY,
                           value      INTEGER     NOT NULL,
                           min_value  INTEGER     NOT NULL,
                           max_value  INTEGER     NOT NULL,
                           instance   TEXT        NOT NULL,
                           created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                       )"""
                )
            print(f"База {DB['host']}:{DB['port']}/{DB['dbname']} доступна, таблица numbers готова", flush=True)
            return
        except psycopg.OperationalError as err:
            print(f"База пока недоступна (попытка {attempt}): {str(err).strip()}", flush=True)
            time.sleep(2)
    raise SystemExit("ОШИБКА: не удалось подключиться к базе данных")


@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield


app = FastAPI(title=APP_TITLE, version=__version__, lifespan=lifespan)


def generate(min_value: int, max_value: int) -> dict:
    if min_value > max_value:
        raise HTTPException(status_code=400, detail="min не может быть больше max")
    value = random.randint(min_value, max_value)
    with connect() as conn:
        row = conn.execute(
            "INSERT INTO numbers (value, min_value, max_value, instance) VALUES (%s, %s, %s, %s) "
            "RETURNING id, created_at",
            (value, min_value, max_value, INSTANCE),
        ).fetchone()
    return {"id": row[0], "value": value, "min": min_value, "max": max_value,
            "instance": INSTANCE, "created_at": row[1].isoformat()}


def history(limit: int = HISTORY_LIMIT) -> tuple[list[dict], int]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, value, min_value, max_value, instance, created_at "
            "FROM numbers ORDER BY id DESC LIMIT %s",
            (limit,),
        ).fetchall()
        total = conn.execute("SELECT count(*) FROM numbers").fetchone()[0]
    items = [{"id": r[0], "value": r[1], "min": r[2], "max": r[3], "instance": r[4],
              "created_at": r[5].isoformat()} for r in rows]
    return items, total


@app.post("/api/numbers")
def api_generate(min: int = Query(DEFAULT_MIN), max: int = Query(DEFAULT_MAX)):
    """Сгенерировать случайное число в диапазоне [min, max] и сохранить его в базе."""
    return generate(min, max)


@app.get("/api/numbers")
def api_history(limit: int = Query(HISTORY_LIMIT, ge=1, le=1000)):
    """Последние сгенерированные числа из базы."""
    items, total = history(limit)
    return {"total": total, "items": items}


@app.get("/api/info")
def api_info():
    """Сведения о запущенном экземпляре приложения."""
    return {"title": APP_TITLE, "version": __version__, "env": APP_ENV, "instance": INSTANCE,
            "default_min": DEFAULT_MIN, "default_max": DEFAULT_MAX, "history_limit": HISTORY_LIMIT,
            "db": f"{DB['host']}:{DB['port']}/{DB['dbname']}"}


@app.get("/health")
def health():
    """Проверка работоспособности: приложение отвечает и база доступна."""
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "db": "ok", "instance": INSTANCE}
    except psycopg.Error as err:
        return JSONResponse({"status": "error", "db": str(err).strip(), "instance": INSTANCE}, status_code=503)


PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", sans-serif; max-width: 760px; margin: 40px auto; color: #222; }}
  h1 {{ margin-bottom: 4px; }}
  .meta {{ color: #666; font-size: 14px; margin-bottom: 24px; }}
  .meta b {{ color: #222; }}
  form {{ display: flex; gap: 10px; align-items: end; margin-bottom: 20px; }}
  label {{ display: flex; flex-direction: column; font-size: 13px; color: #555; }}
  input {{ width: 110px; padding: 6px; font-size: 16px; }}
  button {{ padding: 8px 18px; font-size: 16px; cursor: pointer; }}
  .result {{ font-size: 64px; font-weight: 700; margin: 8px 0 24px; min-height: 76px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  th, td {{ border-bottom: 1px solid #ddd; padding: 6px 8px; text-align: left; }}
  th {{ background: #f4f4f4; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="meta">версия <b>{version}</b> · окружение <b>{env}</b> · экземпляр <b>{instance}</b> · база <b>PostgreSQL</b>, сохранено чисел: <b>{total}</b></div>
<form id="gen">
  <label>от <input name="min" type="number" value="{dmin}"></label>
  <label>до <input name="max" type="number" value="{dmax}"></label>
  <button type="submit">Сгенерировать</button>
</form>
<div class="result" id="result">{last}</div>
<h3>История (последние {limit})</h3>
<table>
<tr><th>№</th><th>Число</th><th>Диапазон</th><th>Экземпляр</th><th>Время</th></tr>
{rows}
</table>
<script>
document.getElementById('gen').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const f = new FormData(e.target);
  const r = await fetch('/api/numbers?min=' + f.get('min') + '&max=' + f.get('max'), {{method: 'POST'}});
  const d = await r.json();
  if (!r.ok) {{ alert(d.detail); return; }}
  location.reload();
}});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    items, total = history()
    rows = "\n".join(
        f"<tr><td>{i['id']}</td><td><b>{i['value']}</b></td><td>{i['min']}…{i['max']}</td>"
        f"<td>{html.escape(i['instance'])}</td><td>{i['created_at'][:19].replace('T', ' ')}</td></tr>"
        for i in items
    ) or '<tr><td colspan="5">Пока пусто — нажмите «Сгенерировать».</td></tr>'
    return PAGE.format(
        title=html.escape(APP_TITLE), version=__version__, env=html.escape(APP_ENV),
        instance=html.escape(INSTANCE), total=total, dmin=DEFAULT_MIN, dmax=DEFAULT_MAX,
        last=items[0]["value"] if items else "—", limit=HISTORY_LIMIT, rows=rows,
    )
