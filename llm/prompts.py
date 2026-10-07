SYSTEM_PROMPT_SUMMARIZATION = (
    "Ты — ассистент для суммаризации текста. "
    "Прочитай текст и выдели главные мысли. "
    "Ответ должен быть кратким (3–5 предложений), "
    "на том же языке, что и исходный текст. "
    "Не добавляй комментариев от себя."
)


def build_messages(user_text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT_SUMMARIZATION},
        {"role": "user", "content": user_text},
    ]