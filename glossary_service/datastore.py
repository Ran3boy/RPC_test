import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


@dataclass
class TermRecord:
    id: str
    term: str
    definition: str
    sources: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    related_ids: List[str] = field(default_factory=list)


class JsonGlossaryStore:
    """Small JSON-backed store.

    Goals:
      - dead simple for a student project
      - deterministic file format (pretty JSON)
      - thread-safe for concurrent gRPC handlers
    """

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
        self._terms: Dict[str, TermRecord] = {}
        self._load()

    def _load(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._terms = {}
            self._save()
            return
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        terms = {}
        for item in data.get("terms", []):
            terms[item["id"]] = TermRecord(**item)
        self._terms = terms

    def _save(self) -> None:
        tmp = {"terms": [asdict(t) for t in sorted(self._terms.values(), key=lambda x: x.term.lower())]}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(tmp, f, ensure_ascii=False, indent=2)

    def list_terms(self) -> List[TermRecord]:
        with self._lock:
            return list(sorted(self._terms.values(), key=lambda t: t.term.lower()))

    def get(self, term_id: str) -> Optional[TermRecord]:
        with self._lock:
            return self._terms.get(term_id)

    def upsert(self, term: TermRecord) -> TermRecord:
        with self._lock:
            if not term.id:
                term.id = str(uuid.uuid4())
            self._terms[term.id] = term
            self._save()
            return term

    def delete(self, term_id: str) -> bool:
        with self._lock:
            if term_id in self._terms:
                del self._terms[term_id]
                # Also clean dangling edges
                for t in self._terms.values():
                    if term_id in t.related_ids:
                        t.related_ids = [x for x in t.related_ids if x != term_id]
                self._save()
                return True
            return False

    def search(self, query: str, limit: int = 20) -> List[TermRecord]:
        q = (query or "").strip().lower()
        if not q:
            return []
        with self._lock:
            hits = []
            for t in self._terms.values():
                hay = f"{t.term}\n{t.definition}\n{' '.join(t.tags)}".lower()
                if q in hay:
                    hits.append(t)
            hits.sort(key=lambda t: (t.term.lower().find(q) if q in t.term.lower() else 9999, t.term.lower()))
            return hits[: max(1, limit)]
