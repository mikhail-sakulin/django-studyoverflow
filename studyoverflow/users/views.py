from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView
from users.forms import UserLoginForm, UserProfileUpdateForm, UserRegisterForm


class UsersTemplateView(TemplateView):
    template_name = "users/users.html"
    extra_context = {"section_of_menu_selected": "users:list"}


class UserRegisterView(SuccessMessageMixin, CreateView):
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("home")
    success_message = "Регистрация успешно завершена!"

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


class CustomLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        user_was_authenticated = request.user.is_authenticated
        response = super().post(request, *args, **kwargs)
        if user_was_authenticated:
            messages.info(self.request, "Вы вышли из аккаунта.")
        return response


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = UserProfileUpdateForm
    template_name = "users/profile.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user
