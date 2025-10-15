from django.urls import path

from . import views


app_name = "users"


urlpatterns = [
    path("", views.UsersTemplateView.as_view(), name="list"),
    path("register/", views.UserRegisterView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
]
