"""Seed the glossary with VKR terms.

Usage:
  python tools/seed.py --host localhost --port 50051

Note: the script adds repo paths to PYTHONPATH so it works without installation.
"""

import argparse
import sys
import uuid
from pathlib import Path

import grpc

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "glossary_service"))

import glossary_pb2  # noqa: E402
import glossary_pb2_grpc  # noqa: E402

TERMS = [
    {
        "term": "Web Components",
        "definition": "Набор веб-стандартов (Custom Elements, Shadow DOM, HTML Templates) для создания переиспользуемых UI-компонентов без привязки к конкретному фреймворку.",
        "tags": ["standard", "frontend", "ui"],
        "sources": ["https://www.w3.org/standards/"],
    },
    {
        "term": "Custom Elements",
        "definition": "Спецификация, позволяющая объявлять собственные HTML-теги и управлять их жизненным циклом.",
        "tags": ["web-components", "standard"],
        "sources": ["https://developer.mozilla.org/"],
    },
    {
        "term": "Shadow DOM",
        "definition": "Механизм инкапсуляции DOM и CSS, изолирующий внутреннюю структуру компонента от внешней страницы.",
        "tags": ["web-components", "standard"],
        "sources": ["https://developer.mozilla.org/"],
    },
    {
        "term": "Virtual DOM",
        "definition": "Подход к построению UI, где изменения сначала применяются к виртуальному дереву, а затем эффективно синхронизируются с реальным DOM.",
        "tags": ["react", "frontend"],
        "sources": ["https://react.dev/"],
    },
    {
        "term": "Hydration",
        "definition": "Процесс «оживления» серверно-отрендеренного HTML на клиенте: привязка обработчиков и состояния.",
        "tags": ["ssr", "frontend"],
        "sources": ["https://nextjs.org/"],
    },
]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=50051)
    args = p.parse_args()

    channel = grpc.insecure_channel(f"{args.host}:{args.port}")
    stub = glossary_pb2_grpc.GlossaryServiceStub(channel)

    ids = {t["term"]: str(uuid.uuid4()) for t in TERMS}
    for t in TERMS:
        related = []
        if t["term"] == "Web Components":
            related = [ids["Custom Elements"], ids["Shadow DOM"]]

        msg = glossary_pb2.Term(
            id=ids[t["term"]],
            term=t["term"],
            definition=t["definition"],
            sources=t.get("sources", []),
            tags=t.get("tags", []),
            related_ids=related,
        )
        stub.UpsertTerm(glossary_pb2.UpsertTermRequest(term=msg))

    print(f"Seeded {len(TERMS)} terms")


if __name__ == "__main__":
    main()
