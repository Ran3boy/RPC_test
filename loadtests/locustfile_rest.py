from locust import HttpUser, task, between
import random

class RestGlossaryUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(3)
    def list_terms(self):
        self.client.get("/api/terms")

    @task(2)
    def get_term(self):
        term_id = random.choice(["1", "2", "3"])
        self.client.get(f"/api/terms/{term_id}")

    @task(1)
    def home(self):
        self.client.get("/")
