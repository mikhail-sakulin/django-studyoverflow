from locust import HttpUser, task


class WebsiteUser(HttpUser):
    host = "http://127.0.0.1:8000"

    @task
    def load_index(self):
        self.client.get("/")

    @task
    def load_posts_list(self):
        self.client.get("/posts/")
