from django import template

register = template.Library()


@register.filter(name="round")
def round_float(value, arg=0):
    arg = int(arg)
    return round(value, arg)
