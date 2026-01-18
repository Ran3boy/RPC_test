import tempfile

from glossary_service.datastore import JsonGlossaryStore, TermRecord


def test_upsert_and_get():
    with tempfile.TemporaryDirectory() as d:
        store = JsonGlossaryStore(f"{d}/terms.json")
        t = TermRecord(id="", term="Test", definition="Def")
        saved = store.upsert(t)
        assert saved.id
        loaded = store.get(saved.id)
        assert loaded is not None
        assert loaded.term == "Test"


def test_search():
    with tempfile.TemporaryDirectory() as d:
        store = JsonGlossaryStore(f"{d}/terms.json")
        store.upsert(TermRecord(id="", term="Web Components", definition="standards"))
        store.upsert(TermRecord(id="", term="React", definition="library"))
        hits = store.search("web", limit=10)
        assert len(hits) == 1
        assert hits[0].term == "Web Components"
