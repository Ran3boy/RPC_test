import time
import random
from locust import User, task, between
from locust.exception import LocustError
import grpc
import grpc.experimental.gevent as grpc_gevent
from grpc_interceptor import ClientInterceptor

# ВАЖНО: патчим grpc под gevent, иначе блокировки
grpc_gevent.init_gevent()

class LocustInterceptor(ClientInterceptor):
    """
    Интерцептор: пробрасывает события в Locust (успех/ошибка/время).
    """
    def __init__(self, environment):
        self.environment = environment

    def intercept(self, method, request_or_iterator, call_details):
        start = time.time()
        try:
            response = method(request_or_iterator, call_details)
            total_ms = (time.time() - start) * 1000
            self.environment.events.request.fire(
                request_type="gRPC",
                name=call_details.method,
                response_time=total_ms,
                response_length=0,
                exception=None,
            )
            return response
        except Exception as e:
            total_ms = (time.time() - start) * 1000
            self.environment.events.request.fire(
                request_type="gRPC",
                name=call_details.method,
                response_time=total_ms,
                response_length=0,
                exception=e,
            )
            raise

class GrpcGlossaryUser(User):
    wait_time = between(0.2, 1.0)

    host = "localhost:50051"  # или из env

    def on_start(self):
        if not self.host:
            raise LocustError("GrpcGlossaryUser.host is not set")

        interceptor = LocustInterceptor(self.environment)
        channel = grpc.insecure_channel(self.host)
        self.channel = grpc.intercept_channel(channel, interceptor)

        # self.stub = GlossaryStub(self.channel)

    @task(7)
    def list_terms(self):
        # req = ListTermsRequest(limit=50)
        # self.stub.ListTerms(req)
        pass

    @task(2)
    def search_terms(self):
        q = random.choice(["web", "dom", "shadow", "component", "framework"])
        # req = SearchTermsRequest(query=q, limit=20)
        # self.stub.SearchTerms(req)
        pass
