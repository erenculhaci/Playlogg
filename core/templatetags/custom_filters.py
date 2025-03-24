from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    return float(value) * float(arg)

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def split(value, arg):
    return value.split(arg)