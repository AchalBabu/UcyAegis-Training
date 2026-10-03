from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Look up a dict value by a variable key inside a template."""
    if not dictionary:
        return []
    return dictionary.get(key, [])
