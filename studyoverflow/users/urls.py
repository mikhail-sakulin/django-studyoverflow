from django.urls import path

from . import views


app_name = "users"


urlpatterns = [path("", views.UsersTemplateView.as_view(), name="list")]
