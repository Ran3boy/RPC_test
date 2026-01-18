from __future__ import annotations

import os
from typing import Optional

import grpc

import sys
from pathlib import Path

# Ensure generated protobuf modules (glossary_pb2*.py) are importable
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

import glossary_pb2
import glossary_pb2_grpc

app = FastAPI(title="VKR Glossary Web Gateway", version="1.0.0")

GLOSSARY_HOST = os.getenv("GLOSSARY_HOST", "glossary")
GLOSSARY_PORT = int(os.getenv("GLOSSARY_PORT", "50051"))


def _stub():
    channel = grpc.insecure_channel(f"{GLOSSARY_HOST}:{GLOSSARY_PORT}")
    return glossary_pb2_grpc.GlossaryServiceStub(channel)


def _html_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang=\"ru\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <style>
    body{{font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 40px; max-width: 960px;}}
    .term{{padding: 12px 0; border-bottom: 1px solid #eee;}}
    code{{background:#f6f8fa; padding:2px 4px; border-radius:4px;}}
    a{{text-decoration:none;}}
    a:hover{{text-decoration:underline;}}
    .tags{{color:#666; font-size: 0.9em;}}
    input{{padding:8px; width: min(420px, 90%);}}
    button{{padding:8px 12px;}}
    pre{{background:#f6f8fa; padding:12px; border-radius:8px; overflow:auto;}}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p><a href=\"/\">Главная</a> · <a href=\"/api/terms\">API</a> · <a href=\"/graph\">Граф</a></p>
  {body}
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def home(q: Optional[str] = None):
    stub = _stub()
    if q:
        res = stub.SearchTerms(glossary_pb2.SearchTermsRequest(query=q, limit=50))
        terms = res.terms
        title = f"Поиск: {q}"
    else:
        res = stub.ListTerms(glossary_pb2.ListTermsRequest(page=1, page_size=200))
        terms = res.terms
        title = "Глоссарий терминов ВКР"

    items = []
    for t in terms:
        tags = (", ".join(t.tags)) if t.tags else ""
        items.append(
            f"<div class='term'>"
            f"<div><a href='/term/{t.id}'><b>{t.term}</b></a></div>"
            f"<div class='tags'>{tags}</div>"
            f"</div>"
        )

    search = """
<form method='get' action='/' style='margin: 16px 0 24px 0;'>
  <input name='q' placeholder='Поиск по термину/определению...' value='{qval}' />
  <button type='submit'>Найти</button>
</form>
""".format(qval=(q or ""))

    body = search + "".join(items) + "<p style='margin-top:20px; color:#666'>Подсказка: открыть /api/terms, чтобы увидеть JSON.</p>"
    return _html_page(title, body)


@app.get("/term/{term_id}", response_class=HTMLResponse)
def term_page(term_id: str):
    stub = _stub()
    try:
        res = stub.GetTerm(glossary_pb2.TermId(id=term_id))
    except grpc.RpcError as e:
        raise HTTPException(status_code=404, detail=e.details())

    t = res.term
    sources = "".join([f"<li><a href='{s}' target='_blank' rel='noreferrer'>{s}</a></li>" for s in t.sources])
    rel = "".join([f"<li><a href='/term/{rid}'><code>{rid}</code></a></li>" for rid in t.related_ids])

    body = f"""
<div class='term'>
  <h2>{t.term}</h2>
  <p>{t.definition}</p>
  <p class='tags'><b>Теги:</b> {", ".join(t.tags) if t.tags else "—"}</p>
  <h3>Источники</h3>
  <ul>{sources if sources else "<li>—</li>"}</ul>
  <h3>Связанные термины (IDs)</h3>
  <ul>{rel if rel else "<li>—</li>"}</ul>
</div>
"""
    return _html_page(t.term, body)


@app.get("/graph", response_class=HTMLResponse)
def graph_page():
    stub = _stub()
    g = stub.GetGraph(glossary_pb2.GetGraphRequest(include_orphans=False))
    # very small inline representation (for a real mindmap you can plug a JS graph lib)
    edges = "\n".join([f"{e.from_id} -> {e.to_id} [{e.label}]" for e in g.edges])
    body = f"""
<p>Текстовое представление графа (для визуализации можно подключить Cytoscape.js / D3.js).</p>
<pre>{edges if edges else "(пока нет связей)"}</pre>
"""
    return _html_page("Граф терминов", body)


# --- JSON API (REST) ---

@app.get("/api/terms")
def api_terms():
    stub = _stub()
    res = stub.ListTerms(glossary_pb2.ListTermsRequest(page=1, page_size=1000))
    return {
        "total": res.total,
        "terms": [
            {
                "id": t.id,
                "term": t.term,
                "definition": t.definition,
                "sources": list(t.sources),
                "tags": list(t.tags),
                "related_ids": list(t.related_ids),
            }
            for t in res.terms
        ],
    }


@app.get("/api/terms/{term_id}")
def api_term(term_id: str):
    stub = _stub()
    try:
        res = stub.GetTerm(glossary_pb2.TermId(id=term_id))
    except grpc.RpcError as e:
        raise HTTPException(status_code=404, detail=e.details())
    t = res.term
    return {
        "id": t.id,
        "term": t.term,
        "definition": t.definition,
        "sources": list(t.sources),
        "tags": list(t.tags),
        "related_ids": list(t.related_ids),
    }
