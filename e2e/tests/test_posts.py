import re

from helpers.data_generators import generate_post_data
from playwright.sync_api import Page, expect


def test_create_edit_delete_post(page: Page, register_and_login_user, posts_page):
    """
    Проверяет сценарий жизненного цикла поста.

    Регистрация пользователя → Создать пост → Проверить наличие в списке постов →
    → Перейти на детальное представление → Редактировать → Проверить изменения →
    → Удалить → Проверить отсутствие в списке постов.

    Фикстура register_and_login_user регистрирует пользователя, логинит его и
    возвращает его данные, через фабрику.
    """
    # 1) Регистрация и логин
    register_and_login_user()

    # 2) Создание поста
    post_data_original = generate_post_data()
    posts_page.create_post(**post_data_original)

    title_original = post_data_original["title"]

    expect(page).to_have_url(re.compile(rf"{posts_page.URL_LIST}"))

    # 3) Проверка наличие поста в списке постов с учетом поиска
    posts_page.search_by_title(title_original)
    expect(page).to_have_url(re.compile(r".*q=.*"))
    expect(page.locator(".title", has_text=title_original)).to_be_visible()

    # 4) Переход на детальную страницу поста из списка постов
    posts_page.open_post_detail(title_original)
    expect(page.locator(".title")).to_have_text(title_original)

    # 5) Редактирование поста
    expect(page.get_by_role("link", name="Редактировать")).to_be_visible()

    post_data_edited = generate_post_data()

    title_edited = post_data_edited["title"]
    content_edited = post_data_edited["content"]
    tags_edited = post_data_edited["tags"]

    posts_page.edit_post_on_detail(
        new_title=title_edited, new_content=content_edited, new_tags=tags_edited
    )

    # 6) Проверка редактирования поста через поиск: новый заголовок находится, а старый - нет
    # Проверка старого заголовка
    posts_page.search_by_title(title_original)
    expect(page.locator(".title", has_text=title_original)).to_have_count(0)

    # Проверка нового заголовка
    posts_page.search_by_title(title_edited)
    expect(page.locator(".title", has_text=title_edited)).to_be_visible()

    expect(page).to_have_url(re.compile(rf"{posts_page.URL_LIST}"))

    # Находится карточка измененного поста
    post_card = page.locator(".card", has=page.locator(".title", has_text=title_edited))

    # В найденной карточке проверяется изменение content
    expect(post_card.locator(".content").filter(has_text=content_edited)).to_be_visible()

    # 7) Переход на детальную страницу поста из списка постов
    posts_page.open_post_detail(title_edited)

    # 8) Удаление поста
    posts_page.delete_post_on_detail()

    expect(page.locator(".alert-info")).to_contain_text("Пост удален.")

    # 9) Проверка удаления через поиск поста
    expect(page).to_have_url(re.compile(rf"{posts_page.URL_LIST}"))

    posts_page.search_by_title(title_original)
    expect(page.locator(".title", has_text=title_edited)).to_have_count(0)
