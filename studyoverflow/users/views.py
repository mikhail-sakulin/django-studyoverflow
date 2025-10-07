from django.views.generic import TemplateView


class UsersTemplateView(TemplateView):
    template_name = "users/users.html"
    extra_context = {"section_of_menu_selected": "users:list"}
