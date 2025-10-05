from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="home"),
    path("posts/", views.PostListView.as_view(), name="post_list"),
    path("create-post/", views.PostCreateView.as_view(), name="create_post"),
    path("users/", views.users, name="users"),
]
