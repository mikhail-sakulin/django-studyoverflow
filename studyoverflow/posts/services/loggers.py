import logging


logger = logging.getLogger(__name__)


def log_post_event(event_type: str, post, user, source: str = "web"):
    """
    Логирует различные события поста. Указывает источник: 'web' или 'api'.

    :param event_type: тип события (создание, обновление, удаление)
    :param post: объект поста
    :param user: объект пользователя
    :param source: источник события ('web' для Django views, 'api' для DRF)
    """
    # Возможные сообщения в зависимости от типа события
    event_messages = {
        "post_create": f"Пост создан: {post.title} (id: {post.pk}).",
        "post_update": f"Пост отредактирован: {post.title} (id: {post.pk}).",
        "post_delete": f"Пост удален: {post.title} (id: {post.pk}).",
    }

    user_id = user.pk if user and user.is_authenticated else None

    # Основные данные лога
    extra_data = {
        "post_id": post.pk,
        "source": source,
        "event_type": event_type,
    }

    # Роль пользователя в действии в зависимости от типа события
    if event_type == "post_create":
        extra_data["author_id"] = user_id
    elif event_type == "post_update":
        extra_data["editor_id"] = user_id
    elif event_type == "post_delete":
        extra_data["deleter_id"] = user_id

    logger.info(event_messages.get(event_type, "Событие поста"), extra=extra_data)
