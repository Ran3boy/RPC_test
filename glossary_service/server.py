from __future__ import annotations

import os
from concurrent import futures
from typing import Tuple

import grpc

import glossary_pb2
import glossary_pb2_grpc

from datastore import JsonGlossaryStore, TermRecord


def _paginate(items, page: int, page_size: int) -> Tuple[list, int, int]:
    page = page if page and page > 0 else 1
    page_size = page_size if page_size and page_size > 0 else 50
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], page, page_size


class GlossaryService(glossary_pb2_grpc.GlossaryServiceServicer):
    def __init__(self, store: JsonGlossaryStore):
        self.store = store

    def UpsertTerm(self, request, context):
        t = request.term
        rec = TermRecord(
            id=t.id,
            term=t.term.strip(),
            definition=t.definition.strip(),
            sources=list(t.sources),
            tags=list(t.tags),
            related_ids=list(t.related_ids),
        )
        if not rec.term:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "term is required")
        if not rec.definition:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "definition is required")
        saved = self.store.upsert(rec)
        return glossary_pb2.UpsertTermResponse(term=_to_pb(saved))

    def GetTerm(self, request, context):
        rec = self.store.get(request.id)
        if not rec:
            context.abort(grpc.StatusCode.NOT_FOUND, "term not found")
        return glossary_pb2.GetTermResponse(term=_to_pb(rec))

    def DeleteTerm(self, request, context):
        ok = self.store.delete(request.id)
        return glossary_pb2.DeleteTermResponse(deleted=ok)

    def ListTerms(self, request, context):
        terms = self.store.list_terms()
        page_terms, page, page_size = _paginate(terms, request.page, request.page_size)
        return glossary_pb2.ListTermsResponse(
            terms=[_to_pb(t) for t in page_terms],
            page=page,
            page_size=page_size,
            total=len(terms),
        )

    def SearchTerms(self, request, context):
        limit = request.limit if request.limit > 0 else 20
        hits = self.store.search(request.query, limit=limit)
        return glossary_pb2.SearchTermsResponse(terms=[_to_pb(t) for t in hits])

    def GetGraph(self, request, context):
        nodes = self.store.list_terms()
        node_by_id = {n.id: n for n in nodes}
        edges = []
        for n in nodes:
            for rid in n.related_ids:
                if rid in node_by_id:
                    edges.append(glossary_pb2.GraphEdge(from_id=n.id, to_id=rid, label="relates_to"))
                elif request.include_orphans:
                    edges.append(glossary_pb2.GraphEdge(from_id=n.id, to_id=rid, label="relates_to"))
        return glossary_pb2.GetGraphResponse(nodes=[_to_pb(n) for n in nodes], edges=edges)


def _to_pb(rec: TermRecord) -> glossary_pb2.Term:
    return glossary_pb2.Term(
        id=rec.id,
        term=rec.term,
        definition=rec.definition,
        sources=list(rec.sources),
        tags=list(rec.tags),
        related_ids=list(rec.related_ids),
    )


def serve() -> None:
    port = int(os.getenv("GRPC_PORT", "50051"))
    data_path = os.getenv("DATA_PATH", "/data/terms.json")

    store = JsonGlossaryStore(data_path)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    glossary_pb2_grpc.add_GlossaryServiceServicer_to_server(GlossaryService(store), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Glossary gRPC server started on :{port}, data: {data_path}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
