from django.views.generic import TemplateView


class UsersTemplateView(TemplateView):
    template_name = "users/users.html"
