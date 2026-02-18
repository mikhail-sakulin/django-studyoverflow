from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def handle_github(user, data):
    """
    Обрабатывает данные пользователя, полученные от GitHub OAuth.

    Логика:
    - Разбивает поле `name` на first_name и last_name.
    - Сохраняет `bio` пользователя.
    - Возвращает URL аватара GitHub (avatar_url) для последующего сохранения.
    """
    full_name = data.get("name", "")
    if full_name:
        parts = full_name.split(" ", 1)
        user.first_name = parts[0]
        if len(parts) > 1:
            user.last_name = parts[1]

    if data.get("bio"):
        user.bio = data["bio"]

    return data.get("avatar_url")


def handle_google(user, data):
    """
    Обрабатывает данные пользователя, полученные от Google OAuth.

    Логика:
    - Устанавливает first_name и last_name из `given_name` и `family_name`.
    - Получает URL аватара (`picture`) и заменяет размер на 1024x1024.
    """
    user.first_name = data.get("given_name", "")
    user.last_name = data.get("family_name", "")
    avatar_url = data.get("picture")

    if not avatar_url:
        return None

    return avatar_url.replace("s96-c", "s1024-c")


def handle_yandex(user, data):
    """
    Обрабатывает данные пользователя, полученные от Yandex OAuth.

    Логика:
    - Устанавливает first_name и last_name.
    - Формирует URL аватара по `default_avatar_id`, если он присутствует.
    """
    user.first_name = data.get("first_name", "")
    user.last_name = data.get("last_name", "")

    avatar_id = data.get("default_avatar_id")
    if avatar_id:
        return f"https://avatars.mds.yandex.net/get-yapic/{avatar_id}/islands-200"
    return None


def handle_vk(user, data):
    """
    Обрабатывает данные пользователя, полученные от VK OAuth.

    Логика:
    - Устанавливает first_name и last_name.
    - Получает URL аватара (`avatar`) и модифицирует его размер на 1080x1080.
    """
    user.first_name = data.get("first_name", "")
    user.last_name = data.get("last_name", "")

    avatar_url = data.get("avatar")
    if not avatar_url:
        return None

    parsed = urlparse(avatar_url)
    query = parse_qs(parsed.query)
    query["cs"] = ["1080x1080"]

    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


SOCIAL_HANDLERS = {
    "github": handle_github,
    "google": handle_google,
    "yandex": handle_yandex,
    "vk": handle_vk,
}
