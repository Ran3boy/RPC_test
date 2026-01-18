from locust import HttpUser, task, between
import random
import string

def rnd_word(n=8):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(n))

class RestGlossaryUser(HttpUser):
    wait_time = between(0.2, 1.0)  # реалистичные паузы

    # 70% лёгкий сценарий: список
    @task(7)
    def list_terms(self):
        self.client.get("/terms", name="GET /terms")

    # 25% тяжелее: поиск
    @task(2)
    def search_terms(self):
        q = random.choice(["web", "dom", "shadow", "component", "framework", rnd_word(5)])
        self.client.get(f"/terms/search?q={q}", name="GET /terms/search")

    # 5% запись (если есть POST)
    @task(1)
    def add_term(self):
        payload = {
            "term": f"term-{rnd_word(6)}",
            "definition": "auto-generated",
            "tags": ["loadtest"]
        }
        self.client.post("/terms", json=payload, name="POST /terms")
