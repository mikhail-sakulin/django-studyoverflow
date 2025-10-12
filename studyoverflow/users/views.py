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


class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = "users/login.html"
