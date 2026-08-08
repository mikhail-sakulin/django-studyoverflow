from helpers.data_generators import generate_comment_data, generate_post_data
from helpers.pages import AuthPage, CommentPage, PostsPage
from playwright.sync_api import Page, expect


def test_create_comment_tree(
    page: Page, browser, base_url, register_and_login_user, posts_page, comment_page, auth_page
):
    """
    Проверяет сценарий комментирования под постом.

    A создаёт пост → B комментирует → A отвечает → B обновляет комментарии →
    → B отвечает на ответ → Проверяется вложенность комментариев.

    Фикстура register_and_login_user регистрирует пользователя, логинит его и
    возвращает его данные, через фабрику.
    """
    # 1) Пользователь A: регистрация, логин, создание поста, логаут

    # Регистрация и логин
    register_and_login_user()

    # Создание поста
    post_data = generate_post_data()
    posts_page.create_post(**post_data)

    post_title = post_data["title"]

    # 2) Пользователь B: регистрация, логин, переход на пост, создание корневого комментария
    with browser.new_context(base_url=base_url) as context_b:
        page_b = context_b.new_page()

        # Инициализация page objects для page_b
        auth_page_b = AuthPage(page_b)
        posts_page_b = PostsPage(page_b)
        comment_page_b = CommentPage(page_b)

        # Регистрация и логин пользователя B
        register_and_login_user(current_auth_page=auth_page_b)

        # user B находит пост и создаёт корневой комментарий
        posts_page_b.search_by_title(post_title)

        posts_page_b.open_post_detail(post_title)

        comment_b_root_content = generate_comment_data()["content"]
        comment_page_b.create_root_comment(comment_b_root_content)

        # 3) User A отвечает на родительский комментарий user B
        posts_page.search_by_title(post_title)
        posts_page.open_post_detail(post_title)

        reply_a_content = generate_comment_data()["content"]
        comment_page.reply_to_comment(comment_b_root_content, reply_a_content)

        # 4) User B отвечает на ответ user A

        # Обновление комментариев
        page_b.get_by_role(role="button", name="Применить").click()

        # Проверка появления текста reply_a_content созданного комментария
        expect(page_b.locator(".comment-content", has_text=reply_a_content)).to_be_visible()

        # Создание ответного комментария
        reply_b_content = generate_comment_data()["content"]
        comment_page_b.reply_to_comment(reply_a_content, reply_b_content)

        # 5) Проверка дерева комментариев через user A

        # Обновление комментариев
        page.get_by_role(role="button", name="Применить").click()

        # Проверка появления текста reply_b_content созданного комментария
        expect(page.locator(".comment-content", has_text=reply_b_content)).to_be_visible()

        # Список из (текст_комментария, уровень_вложенности)
        comments = comment_page.get_comment_texts_with_levels()

        expected_comment_tree = [
            (comment_b_root_content, 0),
            (reply_b_content, 1),
            (reply_a_content, 1),
        ]
        assert comments == expected_comment_tree


def test_edit_delete_comment(
    page: Page, register_and_login_user, auth_page, posts_page, comment_page
):
    """
    Проверяет сценарий создания, редактирования и удаления комментария.

    Регистрация и логин → Создать пост → Создать комментарий →
    → Редактировать комментарий → Удалить комментарий.

    Фикстура register_and_login_user регистрирует пользователя, логинит его и
    возвращает его данные, через фабрику.
    """
    # 1) Регистрация и логин
    register_and_login_user()

    # 2) Создание поста, поиск и открытие его детального представления
    post_data = generate_post_data()
    posts_page.create_post(**post_data)

    post_title = post_data["title"]

    posts_page.search_by_title(post_title)
    posts_page.open_post_detail(post_title)

    # 3) Создание родительского комментария
    original_comment_content = generate_comment_data()["content"]
    comment_page.create_root_comment(original_comment_content)

    # 4) Изменение комментария
    edited_comment_content = generate_comment_data()["content"]
    comment_page.edit_comment(original_comment_content, edited_comment_content)

    expect(page.locator(".comment-content", has_text=original_comment_content)).to_have_count(0)
    expect(page.locator(".comment-content", has_text=edited_comment_content)).to_have_count(1)

    # 5) Удаление комментария
    comment_page.delete_comment(edited_comment_content)
    expect(page.locator(".comment-content", has_text=edited_comment_content)).to_have_count(0)
