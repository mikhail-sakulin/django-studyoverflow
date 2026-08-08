from playwright.sync_api import Locator, Page


class AuthPage:
    """
    Page Object Model для сценариев аутентификации (регистрация, логин, логаут).
    """

    URL_PATH_LOGIN = "/users/login/"
    URL_PATH_REGISTER = "/users/register/"

    def __init__(self, page: Page):
        self.page = page

    def navigate_to_register(self):
        """Переход на страницу регистрации."""
        self.page.goto("/")
        self.page.get_by_role("link", name="Регистрация").click()

    def register(self, username, email, password, first_name="", last_name=""):
        """Регистрация пользователя."""
        self.page.fill("#id_username", username)
        self.page.fill("#id_email", email)
        self.page.fill("#id_password1", password)
        self.page.fill("#id_password2", password)

        if first_name:
            self.page.fill("#id_first_name", first_name)
        if last_name:
            self.page.fill("#id_last_name", last_name)

        self.page.get_by_role("button", name="Регистрация").click()

    def login(self, login_identifier, password):
        """Переход на логин и вход аккаунт."""
        self.page.goto(f"{self.URL_PATH_LOGIN}")
        self.page.fill("#id_username", login_identifier)
        self.page.fill("#id_password", password)
        self.page.get_by_role("button", name="Вход").click()

    def logout(self):
        """Выход из аккаунта."""
        self.page.goto("/")
        self.page.get_by_role("button", name="Выйти").click()


class PersonalProfilePage:
    """
    Page Object Model для личного профиля пользователя.
    """

    URL_PATH_PERSONAL_PROFILE = "/users/profile/me/"

    def __init__(self, page: Page):
        self.page = page

    def go_to_profile(self):
        """Переход в личный профиль."""
        self.page.locator("#profile-button").click()

    def change_password(self, old_password, new_password):
        """Переходит по ссылке смены пароля и меняет пароль."""
        self.page.get_by_role("link", name="Сменить пароль").click()
        self.page.fill("#id_old_password", old_password)
        self.page.fill("#id_new_password1", new_password)
        self.page.fill("#id_new_password2", new_password)
        self.page.get_by_role("button", name="Сменить пароль").click()

    def delete_account(self):
        """Удаляет аккаунт с подтверждением в модальном окне."""
        self.page.get_by_role(role="button", name="Удалить").click()
        self.page.locator("#deleteUserModal .btn-danger").click()

    def click_edit_profile(self):
        """Нажимает кнопку 'Редактировать профиль' и ждёт появления формы."""
        # Ожидание полной загрузки статики, чтобы JS сработал и кнопка отобразила форму
        self.page.wait_for_load_state("load")

        self.page.get_by_role("button", name="Редактировать профиль").click()
        self.page.locator("#edit-form-container").wait_for(state="visible")

    def fill_profile_form(
        self, username=None, first_name=None, last_name=None, email=None, bio=None, date_birth=None
    ):
        """
        Заполняет поля формы редактирования профиля, кроме аватара, поскольку для e2e тестирования
        не поднимается тестовое S3 хранилище.

        Поля, которые не переданы, остаются без изменений.
        """
        if username is not None:
            self.page.fill("#id_username", username)
        if first_name is not None:
            self.page.fill("#id_first_name", first_name)
        if last_name is not None:
            self.page.fill("#id_last_name", last_name)
        if email is not None:
            self.page.fill("#id_email", email)
        if bio is not None:
            self.page.fill("#id_bio", bio)
        if date_birth is not None:
            self.page.fill("#id_date_birth", date_birth)

    def submit_profile_form(self):
        """Нажимает кнопку 'Сохранить изменения' и ждёт сообщения об успехе."""
        self.page.get_by_role("button", name="Сохранить изменения").click()
        self.page.locator(".alert-success").wait_for(state="visible")

    def get_profile_display_data(self):
        """
        Возвращает текущие некоторые отображаемые данные профиля из карточки пользователя.

        Используется для проверки после сохранения.
        """
        # Имя и фамилия
        full_name = (self.page.locator("h6.mb-1").text_content() or "").strip()
        # Если разделителя нет, то вся строка присвоится first_name, если разделитель есть,
        # то ему станет равен _
        first_name, _, last_name = full_name.partition(" ")
        return {
            "username": (self.page.locator(".author-name").text_content() or "").strip(),
            "email": (self.page.locator(".email").text_content() or "").strip(),
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            # "+" - поиск следующего элемента на одном уровне вложенности в CSS
            "date_birth": (
                self.page.locator("span:has-text('Дата рождения:') + span").text_content() or ""
            ).strip(),
            # .bio-scroll p - проверяет p на любом уровне вложенности в .bio-scroll,
            # если совпадений несколько, то вызывается ошибка.
            "bio": (self.page.locator(".bio-scroll p").text_content() or "").strip(),
        }


class PublicProfilePage:
    """
    Page Object Model для просмотра публичного профиля другого пользователя.
    """

    URL_PATH_PUBLIC_PROFILE_WITHOUT_USERNAME = "/users/profile/"

    def __init__(self, page: Page):
        self.page = page

    def go_to_user_profile(self, username: str):
        """Переход на страницу профиля пользователя по его username."""
        self.page.goto(f"{self.URL_PATH_PUBLIC_PROFILE_WITHOUT_USERNAME}{username}/")

    def get_profile_display_data(self):
        """
        Возвращает отображаемые данные из публичного профиля.
        """
        full_name = (self.page.locator("h6.mb-1").text_content() or "").strip()
        first_name, _, last_name = full_name.partition(" ")

        return {
            "username": (self.page.locator(".author-name").text_content() or "").strip(),
            "email": (self.page.locator(".email").text_content() or "").strip(),
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "date_birth": (
                self.page.locator("span:has-text('Дата рождения:') + span").text_content() or ""
            ).strip(),
            "date_joined": (
                self.page.locator("span:has-text('На сайте с:') + span").text_content() or ""
            ).strip(),
            # Текст внутри .col-4 ищется на любом уровне вложенности
            "reputation": (
                self.page.locator(".col-4", has_text="Репутация").locator("h6").text_content() or ""
            ).strip(),
            "posts_count": (
                self.page.locator(".col-4", has_text="Посты").locator("h6").text_content() or ""
            ).strip(),
            "comments_count": (
                self.page.locator(".col-4", has_text="Комментарии").locator("h6").text_content()
                or ""
            ).strip(),
        }

    def edit_button_visible(self) -> bool:
        """Проверяет видимость кнопки 'Редактировать профиль'."""
        return self.page.get_by_role("button", name="Редактировать профиль").is_visible()

    def delete_button_visible(self) -> bool:
        """Проверяет видимость кнопки 'Удалить'."""
        return self.page.get_by_role("button", name="Удалить").is_visible()

    def change_password_link_visible(self) -> bool:
        """Проверяет видимость ссылки 'Сменить пароль'."""
        return self.page.get_by_role("link", name="Сменить пароль").is_visible()


class PostsPage:
    """
    Page Object Model для работы с постами: создание, редактирование, удаление,
    проверка наличия в списке, переход на детальную страницу.
    """

    URL_CREATE = "/posts/create/"
    URL_LIST = "/posts/"

    def __init__(self, page: Page):
        self.page = page

    def navigate_to_create(self):
        """Переход на страницу создания поста."""
        self.page.locator("#header").get_by_role("link", name="Создать пост").click()

    def fill_create_form(self, title: str, content: str, tags: str = ""):
        """Заполняет форму создания поста."""
        self.page.fill("#id_title", title)
        self.page.fill("#id_content", content)
        self.page.fill("#id_tags", tags)

    def submit_create_form(self):
        """Нажимает кнопку 'Отправить' и ждёт редиректа на список постов."""
        self.page.get_by_role("button", name="Отправить").click()

    def create_post(self, title: str, content: str, tags: str):
        """Полный цикл создания поста: переход, заполнение данных, отправка."""
        self.navigate_to_create()
        self.fill_create_form(title, content, tags)
        self.submit_create_form()

    def search_by_title(self, title: str):
        """Вводит заголовок в поле поиска и выполняет поиск."""
        self.page.fill("#base-search", title)

        # Enter нажимается после загрузки страницы
        with self.page.expect_navigation(wait_until="load"):
            self.page.keyboard.press("Enter")

    def open_post_detail(self, title: str):
        """
        На странице списка постов находит карточку с указанным заголовком
        и кликает по ссылке 'Подробнее'.
        """
        card = self.page.locator(".card", has=self.page.locator(f".title:has-text('{title}')"))
        card.locator(".more-link:has-text('Подробнее')").click()
        self.page.wait_for_selector(".title", state="visible")

    def click_edit_on_detail(self):
        self.page.get_by_role("link", name="Редактировать").click()
        self.page.wait_for_selector("#id_title", state="visible")

    def fill_edit_form(
        self, title: str | None = None, content: str | None = None, tags: str | None = None
    ):
        if title is not None:
            self.page.fill("#id_title", title)
        if content is not None:
            self.page.fill("#id_content", content)
        if tags is not None:
            self.page.fill("#id_tags", tags)

    def submit_edit_form(self):
        self.page.get_by_role("button", name="Редактировать").click()
        self.page.wait_for_selector(".title", state="visible")

    def edit_post_on_detail(
        self,
        new_title: str | None = None,
        new_content: str | None = None,
        new_tags: str | None = None,
    ):
        self.click_edit_on_detail()
        self.fill_edit_form(new_title, new_content, new_tags)
        self.submit_edit_form()

    def delete_post_on_detail(self):
        self.page.get_by_role(role="button", name="Удалить").click()
        # Подтверждение удаления в модальном окне
        self.page.locator("#deletePostModal .btn-danger").click()

    def like_detail_post(self) -> Locator:
        """
        Лайкает пост на странице детального представления.

        Повторное нажатие убирает лайк.
        """
        like_btn = self.page.locator(".card.mb-4 .like-button").first
        like_btn.click()
        return like_btn


class CommentPage:
    """
    Page Object Model для работы с комментариями на странице детального представления поста.
    """

    def __init__(self, page: Page):
        self.page = page

    def open_comment_form(self):
        """Открывает форму для создания родительского комментария."""
        self.page.get_by_role("button", name="Комментировать").click()
        self.page.locator("#comment-form-container").wait_for(state="visible")

    def fill_comment_form(self, content):
        """Заполняет поле ввода родительского комментария."""
        self.page.fill("#id_content", content)

    def submit_comment(self, content):
        """Отправляет форму комментария и ждёт появления комментария."""
        self.page.get_by_role("button", name="Отправить").click()
        self.page.locator(".comment-content", has_text=content).wait_for(state="visible")

    def create_root_comment(self, content):
        """Создаёт корневой комментарий."""
        self.open_comment_form()
        self.fill_comment_form(content)
        self.submit_comment(content)

    def reply_to_comment(self, parent_text, reply_content):
        """
        Отвечает на комментарий с текстом parent_text.

        Находит карточку родительского комментария, нажимает 'Ответить',
        заполняет форму и отправляет.
        """
        parent_card = self.page.locator(".card", has_text=parent_text)
        parent_card.get_by_role("button", name="Ответить").click()
        # Форма ответа внутри карточки
        form = parent_card.locator(".reply-form-container")
        form.locator("textarea").fill(reply_content)
        form.get_by_role("button", name="Отправить").click()
        self.page.locator(".comment-content", has_text=reply_content).wait_for(state="visible")

    def edit_comment(self, old_text, new_text):
        """
        Редактирует комментарий с текстом old_text, заменяя его на new_text.
        """
        # Возвращает список элементов, в id которых есть "comment-wrapper"
        card = self.page.locator('[id*="comment-wrapper"]', has_text=old_text)
        card.get_by_role("button", name="Редактировать").click()
        edit_form = card.locator(".edit-form-container")
        edit_form.wait_for(state="visible")
        edit_form.locator("textarea").fill(new_text)
        edit_form.get_by_role("button", name="Сохранить").click()
        self.page.locator(".comment-content", has_text=new_text).wait_for(state="visible")

    def delete_comment(self, comment_text):
        """
        Удаляет комментарий с указанным текстом, подтверждая удаление в диалоговом окне браузера.
        """
        card = self.page.locator('[id*="comment-wrapper"]', has_text=comment_text)

        # Перехват всплывающего окна confirm и автоматическое подтверждение будущего удаления
        self.page.once("dialog", lambda dialog: dialog.accept())

        card.get_by_role("button", name="Удалить").click()

        self.page.locator(".comment-content", has_text=comment_text).wait_for(state="hidden")

    def get_comment_texts_with_levels(self):
        """
        Возвращает список кортежей (текст_комментария, уровень_вложенности).
        Уровень: 0 – корневой, 1 – дочерний.
        """
        # Возвращает список элементов, в id которых есть "comment-wrapper"
        comment_cards = self.page.locator('[id*="comment-wrapper"]').all()
        result = []
        for comment_card in comment_cards:
            text = (comment_card.locator(".comment-content").text_content() or "").strip()
            classes = comment_card.get_attribute("class") or ""
            # Дочерние комментарии имеют класс ms-6
            level = 1 if "ms-6" in classes else 0
            result.append((text, level))
        return result

    def like_comment(self, comment_text: str) -> Locator:
        """
        Лайкает комментарий.

        Повторное нажатие убирает лайк.
        """
        card = self.page.locator(".card", has_text=comment_text)
        like_btn = card.locator(".like-button")
        like_btn.click()
        return like_btn
