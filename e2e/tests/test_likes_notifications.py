import re

from helpers.data_generators import generate_comment_data, generate_post_data
from playwright.sync_api import Page, expect


def test_likes_and_notifications(page: Page, register_and_login_user, posts_page, comment_page):
    """
    Проверяет сценарий постановки лайков посту и комментарию, также проверяются уведомления.

    Регистрация → создание поста → создание комментария →
    → лайк поста → лайк комментария → снятие лайка с поста → снятие лайка с комментария.

    При этом проверяется счётчик уведомлений.

    Фикстура register_and_login_user регистрирует пользователя, логинит его и
    возвращает его данные, через фабрику.
    """
    # 1) Регистрация и логин
    register_and_login_user()

    # Проверка количества уведомлений
    expect(page.locator("#notifications-count")).to_have_text("1")

    # 2) Создание поста
    post_data = generate_post_data()
    posts_page.create_post(**post_data)

    # Уведомления обновляются без перезагрузки страницы через websocket, но
    # для стабильности тестов страница перезагружается
    page.reload()
    expect(page.locator("#notifications-count")).to_have_text("2")

    # Переход на детальное представление поста
    posts_page.search_by_title(post_data["title"])
    posts_page.open_post_detail(post_data["title"])

    # 3) Создание родительского комментария
    comment_content = generate_comment_data()["content"]
    comment_page.create_root_comment(comment_content)

    page.reload()
    expect(page.locator("#notifications-count")).to_have_text("3")

    # 4) Лайк поста
    like_post_btn = posts_page.like_detail_post()

    expect(like_post_btn.locator("i")).to_have_class(re.compile(r"\bbi-heart-fill\b"))

    # Сейчас 1 лайк у поста
    expect(page.locator(".card.mb-4 .like-button .ms-2")).to_have_text("1")

    page.reload()
    expect(page.locator("#notifications-count")).to_have_text("4")

    # 5) Лайк комментария
    like_comment_btn = comment_page.like_comment(comment_content)

    expect(like_comment_btn.locator("i")).to_have_class(re.compile(r"\bbi-heart-fill\b"))

    # Сейчас 1 лайк у комментария
    expect(
        page.locator(".card", has_text=comment_content).locator(".like-button .ms-2")
    ).to_have_text("1")

    page.reload()
    expect(page.locator("#notifications-count")).to_have_text("5")

    # 6) Снятие лайка с поста

    # Повторный клик снимает лайк
    like_post_btn = posts_page.like_detail_post()

    expect(like_post_btn.locator("i")).to_have_class(re.compile(r"\bbi-heart\b"))

    expect(page.locator(".card.mb-4 .like-button .ms-2")).to_have_text("0")

    page.reload()
    expect(page.locator("#notifications-count")).to_have_text("4")

    # 7) Снятие лайка с комментария

    # Повторный клик снимает лайк
    like_comment_btn = comment_page.like_comment(comment_content)

    expect(like_comment_btn.locator("i")).to_have_class(re.compile(r"\bbi-heart\b"))

    expect(
        page.locator(".card", has_text=comment_content).locator(".like-button .ms-2")
    ).to_have_text("0")

    page.reload()
    expect(page.locator("#notifications-count")).to_have_text("3")
