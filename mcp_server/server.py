from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

import yaml  
from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP

from .model import analyze_with_model  # твоя нейронка

# Инициализируем MCP сервер
mcp = FastMCP("code-map-server", json_response=True)

# Путь к YAML карте
ROOT = Path(__file__).resolve().parents[1]
CODE_MAP_PATH = ROOT / "artifacts" / "code_map.yaml"


# ---------- модели ответа ----------

class CodeEntry(BaseModel):
    path: str
    tags: Optional[List[str]] = None
    funcs: Optional[str] = None
    endpoints: Optional[str] = None
    exports: Optional[str] = None
    types: Optional[str] = None
    interfaces: Optional[str] = None
    classes: Optional[List[dict[str, Any]]] = None


class ModelAnalysis(BaseModel):
    question: str = Field(..., description="Запрос пользователя / задача анализа")
    used_files: List[CodeEntry] = Field(
        default_factory=list,
        description="Файлы из code_map.yaml, по которым строился контекст",
    )
    answer: str = Field(..., description="Ответ нейронной модели в текстовом виде")


# ---------- работа с YAML картой ----------

def load_code_map() -> List[dict[str, Any]]:
    if not CODE_MAP_PATH.exists():
        raise FileNotFoundError(
            f"code_map.yaml не найден по пути {CODE_MAP_PATH}. "
            f"Сначала запусти repo_skim.py"
        )

    with CODE_MAP_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    if not isinstance(data, list):
        raise ValueError("Ожидался список записей в code_map.yaml")
    return data


def entry_matches_query(entry: dict[str, Any], query: str) -> bool:
    q = query.lower()
    for key in ("path", "funcs", "endpoints", "exports", "types", "interfaces"):
        v = entry.get(key)
        if isinstance(v, str) and q in v.lower():
            return True
    # по именам классов
    classes = entry.get("classes") or []
    for cls in classes:
        name = cls.get("Name")
        methds = cls.get("methds")
        if isinstance(name, str) and q in name.lower():
            return True
        if isinstance(methds, str) and q in methds.lower():
            return True
    # по тегам
    tags = entry.get("tags") or []
    for t in tags:
        if isinstance(t, str) and q in t.lower():
            return True
    return False


def to_code_entry(entry: dict[str, Any]) -> CodeEntry:
    return CodeEntry(
        path=entry.get("path"),
        tags=entry.get("tags"),
        funcs=entry.get("funcs"),
        endpoints=entry.get("endpoints"),
        exports=entry.get("exports"),
        types=entry.get("types"),
        interfaces=entry.get("interfaces"),
        classes=entry.get("classes"),
    )


# ---------- TOOLS ----------

@mcp.tool()
def list_files(tag: Optional[str] = None, limit: int = 50) -> List[CodeEntry]:
    """
    Вернуть список файлов из code_map.yaml.
    Можно фильтровать по тегу (tags.yml / @tags).
    """
    entries = load_code_map()
    if tag:
        t = tag.lower()
        entries = [
            e
            for e in entries
            if any(isinstance(x, str) and t in x.lower() for x in e.get("tags", []))
        ]
    return [to_code_entry(e) for e in entries[:limit]]


@mcp.tool()
def search_code(query: str, limit: int = 20) -> List[CodeEntry]:
    """
    Полнотекстовый поиск по карте кода.
    Ищет по path, funcs, endpoints, exports, types, interfaces, именам классов и методам.
    """
    entries = load_code_map()
    matched = [e for e in entries if entry_matches_query(e, query)]
    return [to_code_entry(e) for e in matched[:limit]]


@mcp.tool()
def get_file_info(path: str) -> Optional[CodeEntry]:
    """
    Вернуть одну запись по точному path из code_map.yaml.
    """
    entries = load_code_map()
    for e in entries:
        if e.get("path") == path:
            return to_code_entry(e)
    return None


@mcp.tool()
def analyze_with_nn(question: str, max_files: int = 30) -> ModelAnalysis:
    """
    Инструмент верхнего уровня:
    - находит релевантные файлы по вопросу
    - передаёт их в нейронную модель
    - возвращает ответ + список использованных файлов
    """
    entries = load_code_map()
    matched = [e for e in entries if entry_matches_query(e, question)]
    matched = matched[:max_files]

    used_files = [to_code_entry(e) for e in matched]

    # Здесь происходит вызов твоей нейросети
    answer_text = analyze_with_model(question=question, files=used_files)

    return ModelAnalysis(
        question=question,
        used_files=used_files,
        answer=answer_text,
    )


if __name__ == "__main__":
    # для использования через stdio транспорт (ChatGPT, mcp-клиенты и т.п.)
    mcp.run(transport="stdio")
