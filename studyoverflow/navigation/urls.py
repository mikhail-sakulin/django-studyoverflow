from django.urls import path
from navigation import views


urlpatterns = [path("", views.IndexTemplateView.as_view(), name="home")]
