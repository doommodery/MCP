from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    # Это будет использоваться только инструментами типа mypy/IDE,
    # во время исполнения этот импорт НЕ выполнится, цикла не будет.
    from .server import CodeEntry


def analyze_with_model(question: str, files: List["CodeEntry"]) -> str:
    """
    Обёртка над твоей нейросетью.

    Сейчас это заглушка. Здесь ты потом:
    - превращаешь question + files в вход модели
    - вызываешь inference
    - декодируешь ответ в строку
    """
    summary = "\n".join(f"- {f.path}" for f in files)
    return (
        "Пока нейросеть не подключена.\n"
        f"Я бы анализировал вопрос: {question!r} по следующим файлам:\n{summary}"
    )
