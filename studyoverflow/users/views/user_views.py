import logging

from allauth.account.signals import user_signed_up
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from users.forms import (
    UserLoginForm,
    UserPasswordChangeForm,
    UserPasswordResetForm,
    UserProfileUpdateForm,
    UserRegisterForm,
    UserSetPasswordForm,
)
from users.services import (
    can_moderate,
    get_cached_online_user_ids,
)

from .mixins import (
    SocialUserPasswordChangeForbiddenMixin,
    UserHTMXPaginationMixin,
    UserOnlineFilterMixin,
    UserSortMixin,
)


UserModel = get_user_model()

logger = logging.getLogger(__name__)


class UsersListView(UserHTMXPaginationMixin, ListView):
    """
    Страница списка пользователей.

    Использует кеширование первой страницы. Список сортируется по репутации и имени пользователя.
    """

    model = UserModel
    template_name = "users/user_list.html"
    context_object_name = "users"
    extra_context = {"section_of_menu_selected": "users:list"}

    def get_queryset(self):
        cache_key = "users_first_page"
        cache_data = cache.get(cache_key)

        if cache_data is None:
            queryset = super().get_queryset()
            queryset = queryset.order_by("-reputation", "username")
            result = list(queryset[: self.paginate_htmx_by])
            remaining = queryset[self.paginate_htmx_by : self.paginate_htmx_by + 1].exists()
            cache.set(cache_key, {"users": result, "remaining": remaining}, timeout=2)
        else:
            result = cache_data["users"]
            remaining = cache_data["remaining"]

        self.remaining = remaining
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "online_ids": get_cached_online_user_ids(),
                "remaining": self.remaining,
                "offset": 0,
                "limit": self.paginate_htmx_by,
            }
        )
        return context


class UsersListHTMXView(UserHTMXPaginationMixin, UserSortMixin, UserOnlineFilterMixin, ListView):
    """
    HTMX-представление для подгрузки пользователей на страницу списка пользователей.

    Поддерживает:
    - постраничную загрузку;
    - сортировку;
    - фильтрацию по online-статусу.

    Используется для динамического обновления списка пользователей
    без полной перезагрузки страницы.
    """

    model = UserModel
    template_name = "users/_user_grid.html"
    context_object_name = "users"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.filter_by_online(queryset)
        queryset = self.apply_sorting(queryset)
        return self.paginate_queryset(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "online_ids": self.get_online_ids(),
                "remaining": self.remaining,
                "offset": self.offset,
                "limit": self.limit,
            }
        )
        return context


class UserRegisterView(SuccessMessageMixin, CreateView):
    """
    Страница регистрации нового пользователя.

    После успешной регистрации:
    - отправляет сигнал user_signed_up (из allauth.account.signals);
    - выполняет редирект на указанный next URL либо на главную страницу.
    """

    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("home")
    success_message = "Регистрация успешно завершена!"

    def form_valid(self, form):
        response = super().form_valid(form)

        user = self.object

        user_signed_up.send(sender=user.__class__, request=self.request, user=user)
        return response

    def get_success_url(self):
        """Редирект после регистрации."""
        # Редирект на next_url, если задан GET-параметр next
        next_url = self.request.GET.get("next")
        return next_url or self.success_url

    def get_context_data(self, **kwargs):
        """Передает GET-параметр next в шаблон."""
        context = super().get_context_data(**kwargs)
        context["next"] = self.request.GET.get("next")
        return context


class UserLoginView(LoginView):
    """
    Страница входа в аккаунт пользователя.

    После успешного входа отображает приветственное сообщение.
    """

    form_class = UserLoginForm
    template_name = "users/login.html"

    def form_valid(self, form):
        messages.success(self.request, f"Добро пожаловать, {form.get_user().get_username()}!")
        return super().form_valid(form)


class UserLogoutView(LoginRequiredMixin, LogoutView):
    """
    Выход пользователя из аккаунта.

    После успешного выхода отображает информационное сообщение.
    """

    def post(self, request, *args, **kwargs):
        user_was_authenticated = request.user.is_authenticated
        response = super().post(request, *args, **kwargs)
        if user_was_authenticated:
            messages.info(self.request, "Вы вышли из аккаунта.")
        return response


class AuthorProfileView(DetailView):
    """
    Страница с публичным профилем пользователя.

    Использует кеширование данных пользователя.

    Если пользователь открывает собственный профиль, выполняется
    редирект на страницу личного профиля.
    """

    model = UserModel
    template_name = "users/profile_author.html"
    context_object_name = "author"

    def get_object(self, queryset=None):
        username = self.kwargs.get("username")
        cache_key = f"user_profile_{username}"

        author = cache.get(cache_key)

        if not author:
            author = get_object_or_404(UserModel, username=username)
            # кеш 2 сек, чтобы данные быстро обновлялись для наглядности
            cache.set(cache_key, author, timeout=2)

        return author

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.username == request.user.username:
            return redirect("users:my_profile")

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class UserProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Страница редактирования профиля текущего пользователя.
    """

    model = UserModel
    form_class = UserProfileUpdateForm
    template_name = "users/profile_current_user.html"
    success_url = reverse_lazy("users:my_profile")
    context_object_name = "author"
    success_message = "Профиль успешно изменен!"

    def get_object(self, queryset=None):
        return self.request.user


def avatar_preview(request, username):
    """
    Возвращает HTML-фрагмент для просмотра аватара пользователя.

    Используется для отображения аватара в модальном окне.
    """
    author = get_object_or_404(UserModel, username=username)
    return render(request, "users/_avatar_only_for_modal.html", {"author": author})


class UserDeleteView(LoginRequiredMixin, DeleteView):
    """
    Представление удаления аккаунта пользователя.

    После удаления выполняется logout и редирект на главную страницу.
    """

    model = UserModel
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.info(self.request, "Аккаунт удален.")
        return super().form_valid(form)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        logout(request)
        return response


class UserPasswordChangeView(
    LoginRequiredMixin,
    SocialUserPasswordChangeForbiddenMixin,
    SuccessMessageMixin,
    PasswordChangeView,
):
    """
    Представление смены пароля пользователя.

    Для социальных аккаунтов смена пароля запрещена.
    """

    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("users:my_profile")
    template_name = "users/password_change.html"
    success_message = "Пароль успешно изменен!"

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        logger.info(
            f"Пользователь {user.username} успешно сменил пароль.",
            extra={
                "username": user.username,
                "user_id": user.id,
                "event_type": "user_password_change_success",
            },
        )
        return response


class UserPasswordResetView(PasswordResetView):
    """
    Страница запроса восстановления пароля через email.
    """

    form_class = UserPasswordResetForm
    template_name = "users/password_reset_form.html"
    email_template_name = "users/password_reset_email.html"
    success_url = reverse_lazy("users:password_reset_done")


class UserPasswordResetDoneView(PasswordResetDoneView):
    """
    Страница сообщения об отправки email для восстановления пароля.
    """

    template_name = "users/password_reset_done.html"


class UserPasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    """
    Страница установки нового пароля после подтверждения email.
    """

    form_class = UserSetPasswordForm
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")
    success_message = "Пароль успешно восстановлен!"

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.user
        logger.info(
            f"Пользователь {user.username} успешно восстановил пароль через email.",
            extra={
                "username": user.username,
                "user_id": user.pk,
                "event_type": "user_password_reset_confirm_success",
            },
        )
        return response


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Страница завершения процесса восстановления пароля.
    """

    template_name = "users/password_reset_complete.html"


@login_required
@permission_required("users.block_user", raise_exception=True)
def block_user(request, user_id):
    """
    Блокирует пользователя.

    Проверяет права модератора (кто блокирует) и возможность модерации целевого пользователю.
    """
    user = get_object_or_404(UserModel, pk=user_id)

    # Проверка возможности заблокировать целевого пользователя
    if not can_moderate(request.user, user):
        raise PermissionDenied(
            "Нельзя модерировать пользователя с равной или более высокой ролью. / "
            "Нельзя модерировать самого себя."
        )

    if user.is_blocked:
        messages.info(request, f"Пользователь {user.username} уже заблокирован.")
        return redirect(user.get_absolute_url())

    user.is_blocked = True
    user.blocked_at = timezone.now()
    user.blocked_by = request.user
    user.save(update_fields=["is_blocked", "blocked_at", "blocked_by"])

    logger.info(
        f"Модератор {request.user.username} заблокировал пользователя {user.username}.",
        extra={
            "moderator_id": request.user.id,
            "target_user_id": user.id,
            "event_type": "user_blocked",
        },
    )

    messages.success(request, f"Пользователь {user.username} заблокирован.")
    return redirect(user.get_absolute_url())


@login_required
@permission_required("users.block_user", raise_exception=True)
def unblock_user(request, user_id):
    """
    Разблокирует пользователя.

    Проверяет права модератора (кто разблокирует) и возможность
    снятия блокировки целевого пользователю.
    """
    user = get_object_or_404(UserModel, pk=user_id)

    # Проверка возможности разблокировать целевого пользователя
    if not can_moderate(request.user, user):
        raise PermissionDenied(
            "Нельзя модерировать пользователя с равной или более высокой ролью. / "
            "Нельзя модерировать самого себя."
        )

    if not user.is_blocked:
        messages.info(request, f"Пользователь {user.username} не заблокирован.")
        return redirect(user.get_absolute_url())

    user.is_blocked = False
    user.blocked_at = None
    user.blocked_by = None
    user.save(update_fields=["is_blocked", "blocked_at", "blocked_by"])

    logger.info(
        f"Модератор {request.user.username} разблокировал пользователя {user.username}.",
        extra={
            "moderator_id": request.user.pk,
            "target_user_id": user.pk,
            "event_type": "user_unblocked",
        },
    )

    messages.success(request, f"Пользователь {user.username} разблокирован.")
    return redirect(user.get_absolute_url())
