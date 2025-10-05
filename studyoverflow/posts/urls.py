from django.urls import path

from . import views


app_name = "posts"


urlpatterns = [
    path("", views.PostListView.as_view(), name="list"),
    path("create/", views.PostCreateView.as_view(), name="create"),
    path("users/", views.users, name="users"),
]
