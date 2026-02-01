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
from users.services.infrastructure import (
    SocialUserPasswordChangeForbiddenMixin,
    UserHTMXPaginationMixin,
    UserOnlineFilterMixin,
    UserSortMixin,
    can_moderate,
    get_online_user_ids,
)


logger = logging.getLogger(__name__)


class UsersListView(UserHTMXPaginationMixin, UserSortMixin, UserOnlineFilterMixin, ListView):
    model = get_user_model()
    template_name = "users/user_list.html"
    context_object_name = "users"
    extra_context = {"section_of_menu_selected": "users:list"}

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by("-reputation", "username")

        self.remaining = queryset[self.paginate_htmx_by : self.paginate_htmx_by + 1].exists()
        return queryset[: self.paginate_htmx_by]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "online_ids": get_online_user_ids(),
                "remaining": self.remaining,
                "offset": 0,
                "limit": self.paginate_htmx_by,
            }
        )
        return context


class UsersListHTMXView(UserHTMXPaginationMixin, UserSortMixin, UserOnlineFilterMixin, ListView):
    model = get_user_model()
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
        """
        Редирект после регистрации.
        """
        # Редирект на next_url, если задан GET-параметр next
        next_url = self.request.GET.get("next")
        return next_url or self.success_url

    def get_context_data(self, **kwargs):
        """
        Передает GET-параметр next в шаблон.
        """
        context = super().get_context_data(**kwargs)
        context["next"] = self.request.GET.get("next")
        return context


class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = "users/login.html"

    def form_valid(self, form):
        messages.success(self.request, f"Добро пожаловать, {form.get_user().get_username()}!")
        return super().form_valid(form)


class UserLogoutView(LoginRequiredMixin, LogoutView):
    def post(self, request, *args, **kwargs):
        user_was_authenticated = request.user.is_authenticated
        response = super().post(request, *args, **kwargs)
        if user_was_authenticated:
            messages.info(self.request, "Вы вышли из аккаунта.")
        return response


class AuthorProfileView(DetailView):
    model = get_user_model()
    template_name = "users/profile_author.html"
    context_object_name = "author"

    def get_object(self, queryset=None):
        return get_object_or_404(get_user_model(), username=self.kwargs.get("username"))

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.username == request.user.username:
            return redirect("users:my_profile")

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class UserProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = get_user_model()
    form_class = UserProfileUpdateForm
    template_name = "users/profile_current_user.html"
    success_url = reverse_lazy("users:my_profile")
    context_object_name = "author"
    success_message = "Профиль успешно изменен!"

    def get_object(self, queryset=None):
        return self.request.user


def avatar_preview(request, username):
    author = get_object_or_404(get_user_model(), username=username)
    return render(request, "users/_avatar_only_for_modal.html", {"author": author})


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = get_user_model()
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
    form_class = UserPasswordResetForm
    template_name = "users/password_reset_form.html"
    email_template_name = "users/password_reset_email.html"
    success_url = reverse_lazy("users:password_reset_done")


class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/password_reset_done.html"


class UserPasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
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
                "user_id": user.id,
                "event_type": "user_password_reset_confirm_success",
            },
        )
        return response


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "users/password_reset_complete.html"


@login_required
@permission_required("users.block_user", raise_exception=True)
def block_user(request, user_id):
    UserModel = get_user_model()  # noqa: N806
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
    UserModel = get_user_model()  # noqa: N806
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
            "moderator_id": request.user.id,
            "target_user_id": user.id,
            "event_type": "user_unblocked",
        },
    )

    messages.success(request, f"Пользователь {user.username} разблокирован.")
    return redirect(user.get_absolute_url())
