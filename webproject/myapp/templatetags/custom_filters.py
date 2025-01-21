# myapp/templatetags/custom_filters.py
from django import template

register = template.Library()


@register.filter
def get(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_item(value, index):
    """Получение элемента по индексу для списков и элементов по ключу для словарей"""
    try:
        return value[index]
    except (IndexError, KeyError):
        return None


@register.filter
def verdict_class(value):
    if value == 'failed':
        return 'failed'
    elif value == 'solved':
        return 'solved'
    elif value == 'in_progress':
        return 'in-progress'
    else:
        return 'not-attempted'
