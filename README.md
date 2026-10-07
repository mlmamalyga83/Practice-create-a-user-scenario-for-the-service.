# LLM Summarizer

Минимальный сервис суммаризации текста через LLM (OpenAI). Реализован как pipeline из 6 слоёв: валидация, кеш, промпт-билдер, вызов модели, пост-обработка, ответ.

## Требования

- Python 3.9+
- API-ключ OpenAI (или совместимый эндпоинт)

## Установка

```bash
git clone <repo-url>
cd my_llm_service
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

Создайте `.env` в корне проекта:

```ini
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.7
LLM_TIMEOUT=30
CACHE_TTL=600
MAX_RETRIES=3
MAX_MESSAGE_LENGTH=1000
```

## Запуск

```bash
python main.py
```

Сервис будет доступен на `http://localhost:8000`. Документация по API — `http://localhost:8000/docs`.

## Примеры запросов

### Успешный запрос

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Искусственный интеллект (ИИ) — это область компьютерных наук, занимающаяся созданием систем, способных выполнять задачи, требующие человеческого интеллекта. Это включает обучение, рассуждение, распознавание речи, компьютерное зрение и многое другое. Современные достижения в глубоком обучении привели к значительному прогрессу в NLP, компьютерном зрении и генеративном ИИ. Крупные языковые модели, такие как GPT, демонстрируют впечатляющие способности к пониманию и генерации текста, близкого к человеческому."}'
```

Ответ (200):
```json
{
  "response": "Искусственный интеллект — область компьютерных наук, создающая системы для задач, требующих человеческого интеллекта. Современные достижения в глубоком обучении привели к прогрессу в NLP и компьютерном зрении.",
  "cached": false,
  "model": "gpt-3.5-turbo"
}
```

### Повторный запрос (из кеша)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Искусственный интеллект (ИИ) — это область компьютерных наук..."}'
```

Ответ (200) с `cached: true`.

### Ошибка валидации

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{}'
```

Ответ (422):
```json
{
  "error": "VALIDATION_ERROR",
  "detail": "Поле 'body.message': Field required",
  "status_code": 422
}
```

### Превышение длины

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "a" * 1001}'
```

Ответ (422):
```json
{
  "error": "VALIDATION_ERROR",
  "detail": "Поле 'body.message': String should have at most 1000 characters",
  "status_code": 422
}
```

## Структура проекта

```
my_llm_service/
├── api/
│   ├── __init__.py
│   ├── routes.py          # эндпоинт POST /chat
│   └── models.py          # Pydantic схемы
├── services/
│   ├── __init__.py
│   └── orchestrator.py    # оркестратор pipeline
├── llm/
│   ├── __init__.py
│   ├── client.py          # вызов OpenAI API, ретраи, таймаут
│   └── prompts.py         # системный промпт, build_messages()
├── cache/
│   ├── __init__.py
│   └── ttl_cache.py       # in-memory кеш с TTL
├── config/
│   ├── __init__.py
│   └── settings.py        # конфигурация из .env
├── tests/
│   └── checklist.md       # чек-лист проверок
├── logs/                  # файлы логов (создаются при запуске)
├── main.py                # точка входа
├── requirements.txt
└── README.md
```

## Pipeline

| Слой | Назначение |
|------|-----------|
| API/валидация | Проверка входных данных (обязательное поле, ≤1000 символов) |
| Кеш | Поиск идентичного запроса в in-memory хранилище (TTL 10 мин) |
| Prompt Builder | Формирование системного промпта суммаризации + user message |
| Вызов LLM | HTTP-запрос к OpenAI API через httpx async, 3 ретрая, таймаут 30с |
| Пост-обработка | Очистка ответа, проверка пустоты |
| Формирование ответа | Упаковка в JSON с метками cached/model |

## Тестирование

Все сценарии проверки — в `tests/checklist.md`.

```bash
# 1. Корректный запрос
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d @tests/fixtures/valid_request.json

# 2. Ошибка валидации
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{}'

# 3. Fallback (отключить интернет)
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"Тест"}'
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| `OPENAI_API_KEY` | — | API-ключ OpenAI |
| `LLM_MODEL` | gpt-3.5-turbo | Модель LLM |
| `LLM_TEMPERATURE` | 0.7 | Температура модели |
| `LLM_TIMEOUT` | 30 | Таймаут запроса (сек) |
| `CACHE_TTL` | 600 | Время жизни кеша (сек) |
| `MAX_RETRIES` | 3 | Количество попыток вызова LLM |
| `MAX_MESSAGE_LENGTH` | 1000 | Макс. длина сообщения (символов) |