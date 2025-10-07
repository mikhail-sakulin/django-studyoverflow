from django import template
from navigation.menu import menu


register = template.Library()


@register.simple_tag()
def get_menu_for_header():
    """
    Simple_tag для передачи menu в base.html.
    """
    return menu
