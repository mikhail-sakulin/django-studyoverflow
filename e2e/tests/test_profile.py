import re

from playwright.sync_api import Page, expect


def test_edit_profile(page: Page, register_and_login_user, personal_profile_page):
    """
    Проверяет сценарий редактирования профиля.

    Регистрация → Логин → Переход в профиль → Нажать "Редактировать профиль" →
    → Заполнить форму новыми данными → Сохранить → Проверить изменения в профиле.

    Фикстура register_and_login_user регистрирует пользователя, логинит его и
    возвращает его данные, через фабрику.
    """
    # 1) Регистрация и логин
    register_data = register_and_login_user()
    username = register_data["username"]
    email = register_data["email"]

    # 2) Переход в профиль
    personal_profile_page.go_to_profile()
    expect(page).to_have_url(re.compile(rf"{personal_profile_page.URL_PATH_PERSONAL_PROFILE}$"))
    expect(page.get_by_text(username)).to_be_visible()

    # 3) Редактирование профиля
    personal_profile_page.click_edit_profile()

    # Новые данные
    new_first_name = "Иван"
    new_last_name = "Иванов"
    new_email = f"new_{email}"
    new_bio = "Биография пользователя."
    new_date_birth = "1990-05-15"

    personal_profile_page.fill_profile_form(
        first_name=new_first_name,
        last_name=new_last_name,
        email=new_email,
        bio=new_bio,
        date_birth=new_date_birth,
    )

    personal_profile_page.submit_profile_form()
    expect(page.locator(".alert-success")).to_contain_text("Профиль успешно изменен!")

    # 4) Проверка изменений в профиле пользователя
    # 15.05.1990
    expected_date_display = re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3.\2.\1", new_date_birth)

    display_data_after_reload = personal_profile_page.get_profile_display_data()
    assert display_data_after_reload["first_name"] == new_first_name
    assert display_data_after_reload["last_name"] == new_last_name
    assert display_data_after_reload["email"] == new_email
    assert display_data_after_reload["bio"] == new_bio
    assert display_data_after_reload["date_birth"] == expected_date_display


def test_view_other_profile(create_registered_user, register_and_login_user, public_profile_page):
    """
    Проверяет просмотр чужого профиля.

    User A → User B → User A заходит и проверяет профиль User B:
    - видит личные данные User B и счетчики;
    - не видит кнопок редактировать, удалить, сменить пароль.

    Фикстура create_registered_user регистрирует пользователя и возвращает его данные,
    через фабрику.

    Фикстура register_and_login_user регистрирует пользователя, логинит его и
    возвращает его данные, через фабрику.
    """
    # 1) Регистрация пользователя B
    data_b = create_registered_user(first_name="Петр", last_name="Петров")
    username_b = data_b["username"]
    email_b = data_b["email"]
    first_name_b = data_b["first_name"]
    last_name_b = data_b["last_name"]

    # 2) Регистрация и логин пользователя A
    register_and_login_user()

    # 3) Переход на профиль B
    public_profile_page.go_to_user_profile(username_b)

    # 4) Проверка отображаемых данных профиля B
    data = public_profile_page.get_profile_display_data()
    assert data["username"] == username_b
    assert data["email"] == email_b
    assert data["first_name"].strip() == first_name_b
    assert data["last_name"].strip() == last_name_b

    # Поля-счетчики видны
    assert int(data["reputation"]) == 0
    assert int(data["posts_count"]) == 0
    assert int(data["comments_count"]) == 0

    # Кнопки изменения и удаления аккаунта не видны
    assert not public_profile_page.edit_button_visible()
    assert not public_profile_page.delete_button_visible()
    assert not public_profile_page.change_password_link_visible()
