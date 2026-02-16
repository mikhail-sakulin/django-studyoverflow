from django import template
from navigation.menu import MENU


register = template.Library()


@register.simple_tag()
def get_menu_for_header():
    """Simple_tag для передачи MENU в base.html."""
    return MENU
