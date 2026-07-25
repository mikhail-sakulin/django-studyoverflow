# SimpleNamespace создает пустой объект, к атрибутам которого можно обращаться, stub (легкий мок)
from types import SimpleNamespace

import pytest
from users.models import User
from users.services import can_moderate, is_author_or_moderator


@pytest.mark.django_db
class TestCanModerate:
    def test_can_moderate_same_user(self, user_factory):
        """Если actor и target — один и тот же пользователь, модерировать нельзя."""
        user = user_factory(role=User.Role.ADMIN)

        assert can_moderate(user, user) is False

    @pytest.mark.parametrize(
        ("actor_role", "target_role", "expected"),
        [
            (User.Role.ADMIN, User.Role.USER, True),
            (User.Role.ADMIN, User.Role.ADMIN, False),
            (User.Role.ADMIN, User.Role.MODERATOR, True),
            (User.Role.MODERATOR, User.Role.ADMIN, False),
            (User.Role.MODERATOR, User.Role.MODERATOR, False),
            (User.Role.STAFF_VIEWER, User.Role.USER, False),
        ],
    )
    def test_can_moderate_roles(self, user_factory, actor_role, target_role, expected):
        """Проверяет приоритеты ролей при модерации пользователей с разными ролями."""
        actor = user_factory(role=actor_role)
        target = user_factory(role=target_role)

        assert can_moderate(actor, target) is expected


@pytest.mark.django_db
class TestIsAuthorOrModerator:
    def test_unauthenticated_user(self):
        """Неаутентифицированный пользователь не имеет прав на изменение объекта."""
        user = SimpleNamespace(is_authenticated=False)
        obj = SimpleNamespace(author_id=1)

        assert is_author_or_moderator(user, obj) is False

    @pytest.mark.parametrize("attr_name", ["author_id", "user_id"])
    def test_user_is_author(self, user_factory, mocker, attr_name):
        """
        Пользователь получает доступ, если является автором объекта,
        ему не нужно иметь прав модератора.
        """
        # Используется factory_boy, чтобы у user были свойство .is_authenticated==True и
        # метод .has_perm(perm)
        user = user_factory()
        # Замена метода has_perm у конкретно этого объекта user на mock,
        # в отличие от user.has_perm = MagicMock() у текущей реализации mock с has_perm будет
        # автоматически убран у user после завершения текущего теста.
        #
        # При вызове has_perm после мока вернется новый MagicMock() (bool(MagicMock()) == True)
        mock_has_perm = mocker.patch.object(user, "has_perm")

        obj = SimpleNamespace(**{attr_name: user.pk})

        assert is_author_or_moderator(user, obj, permission_required="posts.moderate_post") is True
        # Проверка, что проверки прав модератора не было, а достаточно было только
        # авторства пользователя
        mock_has_perm.assert_not_called()

    def test_user_is_moderator_with_permission(self, user_factory, mocker):
        """Пользователь получает доступ, если он не автор, но имеет нужный permission."""
        user = user_factory()
        mocker.patch.object(user, "has_perm", return_value=True)
        # Задается, что user точно не автор obj
        obj = SimpleNamespace(author_id=user.pk + 1)

        assert is_author_or_moderator(user, obj, permission_required="posts.moderate_post") is True
        # Проверяется, что тест прошел успешно, так как user не автор obj, но имеет
        # нужное разрешение на модерацию obj.
        user.has_perm.assert_called_once_with("posts.moderate_post")

    def test_user_has_no_rights(self, user_factory, mocker):
        """Пользователь не автор и не имеет разрешения на модерацию obj."""
        user = user_factory()
        mocker.patch.object(user, "has_perm", return_value=False)
        obj = SimpleNamespace(author_id=user.pk + 1)

        assert is_author_or_moderator(user, obj, permission_required="posts.moderate_post") is False
        user.has_perm.assert_called_once_with("posts.moderate_post")

    def test_no_permission_required_and_not_author(self, user_factory):
        """Если разрешение не передано и пользователь не автор, то модерация запрещена."""
        user = user_factory()
        obj = SimpleNamespace(author_id=user.pk + 1)

        assert is_author_or_moderator(user, obj) is False
