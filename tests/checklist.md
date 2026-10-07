# Чек-лист проверок

| № | Сценарий | Ожидание | Результат |
|---|----------|----------|-----------|
| 1 | **Корректный запрос** — POST /chat с валидным текстом | 200, response не пустой, cached: false |  |
| 2 | **Повторный запрос** — тот же текст, те же параметры | 200, тот же response, cached: true |  |
| 3 | **Пустое тело** — POST /chat {} | 422, error: VALIDATION_ERROR |  |
| 4 | **Превышение длины** — message из 1001 символа | 422, detail содержит "1000" |  |
| 5 | **Сбой сети** — отключить интернет / заблокировать api.openai.com | 503, response == fallback, в логах 3 ретрая |  |
| 6 | **Таймаут** — эмуляция через hosts (127.0.0.1 api.openai.com) | 503, fallback, в логах 3 ретрая с timeout |  |
| 7 | **Сбой модели (500)** — подменить URL на фейковый сервер | 503, fallback, 3 ретрая |  |
| 8 | **Неверный API-ключ** — sk-111111 в .env | 503, fallback, 1 попытка в логах (без ретраев) |  |

## Инструкция по эмуляции сценариев

### Сценарий 5 — сбой сети
```bash
# Windows: отключить сетевой адаптер или
# добавить в C:\Windows\System32\drivers\etc\hosts:
127.0.0.1 api.openai.com
```

### Сценарий 6 — таймаут
```bash
# Добавить в hosts (соединение будет висеть, т.к. нет локального сервера на 443 порту):
127.0.0.1 api.openai.com
```

### Сценарий 7 — 500 от API
```bash
# Быстрый фейковый сервер на Python:
python -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(500)
        self.end_headers()
HTTPServer(('', 443), H).serve_forever()
"
# Или перенаправить запросы через hosts
```

### Сценарий 8 — неверный ключ
```bash
# В .env:
OPENAI_API_KEY=sk-111111
# Перезапустить сервис
```

## Логи

Все логи пишутся в `logs/` в формате JSON. Пример строки лога:
```json
{"timestamp": "2026-10-07T12:00:00.000Z", "level": "INFO", "event": "cache_hit", "ttl_remaining": 423, "duration_ms": 0.3}
```

Проверка:
```bash
# После тестов — grep по событиям:
find logs -name "*.log" -exec grep "cache_hit\|llm_call_retry\|fallback_used" {} \;
```