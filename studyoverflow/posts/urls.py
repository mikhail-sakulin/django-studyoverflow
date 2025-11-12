from django.urls import path

from . import views


app_name = "posts"


urlpatterns = [
    path("", views.PostListView.as_view(), name="list"),
    path("create/", views.PostCreateView.as_view(), name="create"),
    path("<int:pk>/<slug:slug>/", views.PostDetailView.as_view(), name="detail"),
    path("edit/<int:pk>/<slug:slug>/", views.PostUpdateView.as_view(), name="edit"),
    path(
        "<int:post_pk>/<slug:post_slug>/comments/",
        views.CommentListView.as_view(),
        name="comment_list",
    ),
    path(
        "<int:post_pk>/<slug:post_slug>/comments/root/create/",
        views.CommentRootCreateView.as_view(),
        name="comment_root_create",
    ),
    path(
        "<int:post_pk>/<slug:post_slug>/comments/child/create/",
        views.CommentChildCreateView.as_view(),
        name="comment_child_create",
    ),
    path(
        "<int:post_pk>/<slug:post_slug>/comments/<int:comment_pk>/update/",
        views.CommentUpdateView.as_view(),
        name="comment_update",
    ),
    path(
        "<int:post_pk>/<slug:post_slug>/comments/<int:comment_pk>/delete/",
        views.CommentDeleteView.as_view(),
        name="comment_delete",
    ),
]
