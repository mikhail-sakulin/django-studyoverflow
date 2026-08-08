import re

from playwright.sync_api import Page, expect


# BASE_URL задается в environment: docker-compose.e2e.yml


def test_full_auth_lifecycle(page: Page, create_registered_user, auth_page, personal_profile_page):
    """
    Проверяет сценарий полного жизненного цикла учетной записи.

    Регистрация → Логин → Смена пароля → Выход → Попытка входа со старым паролем (ошибка) →
    → Вход с новым паролем → Удаление аккаунта → Попытка входа после удаления (ошибка).

    Фикстура create_registered_user регистрирует пользователя и возвращает его данные,
    через фабрику.
    """
    # 1) Регистрация
    user_data = create_registered_user(first_name="Иван", last_name="Иванов")

    username = user_data["username"]
    email = user_data["email"]
    old_password = user_data["password"]
    new_password = "NewPassword123"

    # После регистрации редирект на "home"
    #
    # BASE_URL задан http://nginx:80, а после редиректа браузер покажет http://nginx/,
    # поэтому используется re.
    #
    # re.compile() - создает регулярное выражение, playwright сравнивает маршрут на соответствие
    # именно регулярному выражению.
    # Если задать строку, то с учетом BASE_URL будет проверяться
    # полное соответствие путей, через re будет проверяться частичное вхождение.
    #
    # .to_have_url умеет работать с регулярными выражениями, но их ему нельзя передать как r-строку
    expect(page).to_have_url(re.compile(r"/$"))
    expect(page.get_by_role(role="link", name="Войти")).to_be_visible()

    # 2) Логин по username
    auth_page.login(login_identifier=username, password=old_password)

    # После логина редирект обратно на главную страницу
    expect(page).to_have_url(re.compile(r"/$"))
    expect(page.locator("#profile-button")).to_be_visible()

    # 3) Переход в профиль
    personal_profile_page.go_to_profile()

    expect(page).to_have_url(re.compile(rf"{personal_profile_page.URL_PATH_PERSONAL_PROFILE}$"))
    # Ищет на открывшейся странице профиля любой текстовый блок, внутри которого написан username
    expect(page.get_by_text(username)).to_be_visible()

    # 4) Смена пароля
    personal_profile_page.change_password(old_password=old_password, new_password=new_password)

    # .locator(...) - находит элемент с CSS-классом alert-success
    # .to_contain_text(...) - запускает поиск элемента, ждет его появления и проверяет текст
    expect(page.locator(".alert-success")).to_contain_text("Пароль успешно изменен!")

    # 5) Выход из аккаунта
    auth_page.logout()

    expect(page).to_have_url(re.compile(r"/$"))
    expect(page.get_by_role("link", name="Войти")).to_be_visible()

    # 6) Попытка входа в аккаунт со старым паролем
    auth_page.login(login_identifier=email, password=old_password)

    expect(page.locator(".text-danger")).to_contain_text("неверный пароль")

    # 7) Вход с новым паролем по email
    auth_page.login(login_identifier=email, password=new_password)

    expect(page.locator("#profile-button")).to_be_visible()

    # 8) Удаление аккаунта
    personal_profile_page.go_to_profile()

    expect(page).to_have_url(re.compile(rf"{personal_profile_page.URL_PATH_PERSONAL_PROFILE}$"))

    personal_profile_page.delete_account()

    # После удаления редирект на главную с сообщением
    expect(page).to_have_url(re.compile(r"/$"))
    expect(page.locator(".alert-info")).to_contain_text("Аккаунт удален.")
    expect(page.get_by_role("link", name="Войти")).to_be_visible()

    # 9) Попытка входа после удаления аккаунта
    auth_page.login(login_identifier=username, password=new_password)

    expect(page.locator(".text-danger")).to_contain_text(
        "Неверное имя пользователя (или email) или неверный пароль."
    )
