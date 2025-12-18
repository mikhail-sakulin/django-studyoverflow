from django.urls import path

from . import views


app_name = "users"


urlpatterns = [
    path("", views.UsersListView.as_view(), name="list"),
    path("list-htmx/", views.UsersListHTMXView.as_view(), name="list_htmx"),
    path("register/", views.UserRegisterView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("delete/", views.UserDeleteView.as_view(), name="delete"),
    path("profile/me/", views.UserProfileUpdateView.as_view(), name="my_profile"),
    path("profile/<slug:username>/", views.AuthorProfileView.as_view(), name="profile"),
    path("avatar/<slug:username>/preview/", views.avatar_preview, name="avatar_preview"),
    path("password-change/", views.UserPasswordChangeView.as_view(), name="password_change"),
    path("password-reset/", views.UserPasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        views.UserPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        views.UserPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        views.UserPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
