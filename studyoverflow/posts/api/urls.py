from posts.api import views
from rest_framework.routers import SimpleRouter


router = SimpleRouter()
router.register("posts", views.PostViewSet, basename="posts")

urlpatterns = router.urls
