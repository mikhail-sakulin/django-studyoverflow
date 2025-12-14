from django.urls import path

from . import views


app_name = "notifications"


urlpatterns = [
    path("", views.NotificationTemplateView.as_view(), name="base"),
    path("list/", views.NotificationListView.as_view(), name="list"),
    path("mark-read/<int:pk>/", views.NotificationMarkReadView.as_view(), name="mark_read"),
    path("mark-read-all/", views.NotificationMarkAllReadView.as_view(), name="mark_all_read"),
    path("delete/<int:pk>/", views.NotificationDeleteView.as_view(), name="delete"),
    path("delete-all/", views.NotificationDeleteAllView.as_view(), name="delete_all"),
]
