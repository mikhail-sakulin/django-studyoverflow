import uuid


def generate_user_register_data():
    """Создает и возвращает данные, необходимые для регистрации пользователя."""
    random_id = str(uuid.uuid4())[:8]
    return {
        "username": f"e2e_user_{random_id}",
        "email": f"user_{random_id}@example.com",
        "password": "StrongPassword123",
    }


def generate_post_data():
    """Создает и возвращает данные для создания поста."""
    return {
        "title": uuid.uuid4().hex,  # 32 символа
        "content": uuid.uuid4().hex,  # 32 символа
        "tags": " ".join([uuid.uuid4().hex[:10]]),
    }


def generate_comment_data():
    """Создает и возвращает данные для комментария."""
    return {"content": f"Комментарий {uuid.uuid4().hex[:20]}"}
