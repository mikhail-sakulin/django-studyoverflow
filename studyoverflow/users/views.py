from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from users.forms import UserLoginForm, UserRegisterForm


class UsersTemplateView(TemplateView):
    template_name = "users/users.html"
    extra_context = {"section_of_menu_selected": "users:list"}


class UserRegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("home")

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
