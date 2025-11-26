from django.urls import path

from . import views


app_name = "users"


urlpatterns = [
    path("", views.UsersTemplateView.as_view(), name="list"),
    path("register/", views.UserRegisterView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("profile/me/", views.UserProfileUpdateView.as_view(), name="my_profile"),
    path("profile/<slug:username>/", views.AuthorProfileView.as_view(), name="profile"),
]
