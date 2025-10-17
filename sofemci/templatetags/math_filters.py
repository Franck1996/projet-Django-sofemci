# sofemci/templatetags/math_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def div(value, arg):
    """Divise value par arg"""
    try:
        if isinstance(value, (int, float, Decimal)) and isinstance(arg, (int, float, Decimal)):
            result = float(value) / float(arg)
            return result
        return 0
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """Multiplie value par arg"""
    try:
        if isinstance(value, (int, float, Decimal)) and isinstance(arg, (int, float, Decimal)):
            return float(value) * float(arg)
        return 0
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Calcule le pourcentage de value par rapport à total"""
    try:
        if total and float(total) != 0:
            return (float(value) / float(total)) * 100
        return 0
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def safe_div(value, arg):
    """Division sécurisée qui retourne 0 en cas d'erreur"""
    try:
        if float(arg) != 0:
            return float(value) / float(arg)
        return 0
    except (ValueError, ZeroDivisionError, TypeError):
        return 0