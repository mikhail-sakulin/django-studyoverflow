from posts.api import views
from posts.api.views import CommentViewSet
from rest_framework.routers import SimpleRouter
from rest_framework_nested import routers


router = SimpleRouter()
router.register("posts", views.PostViewSet, basename="posts")
router.register("tags", views.TagReadOnlyViewSet, basename="tags")

posts_router = routers.NestedSimpleRouter(router, "posts", lookup="post")
posts_router.register("comments", CommentViewSet, basename="post-comments")

urlpatterns = [
    *router.urls,
    *posts_router.urls,
]
