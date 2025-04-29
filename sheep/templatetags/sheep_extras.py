from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to access dictionary values by key.
    Usage: {{ dict|get_item:key }}
    """
    return dictionary.get(key, None)
