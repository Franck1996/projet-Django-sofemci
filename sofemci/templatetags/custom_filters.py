# sofemci/templatetags/custom_filters.py
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from decimal import Decimal

register = template.Library()

@register.filter
def format_kg(value):
    """Formate un poids en kg avec séparateurs de milliers"""
    if value is None:
        return "0 kg"
    try:
        return f"{intcomma(int(value))} kg"
    except (ValueError, TypeError):
        return f"{value} kg"

@register.filter
def format_percentage(value):
    """Formate un pourcentage avec 1 décimale"""
    if value is None:
        return "0%"
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return f"{value}%"

@register.filter
def format_temperature(value):
    """Formate une température avec unité"""
    if value is None:
        return "- °C"
    try:
        return f"{float(value):.1f} °C"
    except (ValueError, TypeError):
        return f"{value} °C"

@register.filter
def format_currency(value):
    """Formate une valeur monétaire"""
    if value is None:
        return "0 FCFA"
    try:
        return f"{intcomma(int(value))} FCFA"
    except (ValueError, TypeError):
        return f"{value} FCFA"

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par clé"""
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """Multiplie la valeur par l'argument"""
    try:
        return Decimal(value) * Decimal(arg)
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return 0

@register.filter
def divide(value, arg):
    """Divise la valeur par l'argument"""
    try:
        if Decimal(arg) == 0:
            return 0
        return Decimal(value) / Decimal(arg)
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return 0

@register.filter
def subtract(value, arg):
    """Soustrait l'argument de la valeur"""
    try:
        return Decimal(value) - Decimal(arg)
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return value

@register.filter
def add(value, arg):
    """Additionne la valeur et l'argument"""
    try:
        return Decimal(value) + Decimal(arg)
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return value

@register.filter
def duration_format(minutes):
    """Formate une durée en minutes en heures:minutes"""
    if minutes is None:
        return "0h00"
    try:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h{mins:02d}"
    except (ValueError, TypeError):
        return f"{minutes} min"

@register.filter
def machine_status_class(status):
    """Retourne la classe CSS pour le statut d'une machine"""
    status_classes = {
        'actif': 'success',
        'maintenance': 'warning',
        'arret': 'secondary',
        'panne': 'danger',
    }
    return status_classes.get(status, 'secondary')

@register.filter
def alert_level_class(level):
    """Retourne la classe CSS pour le niveau d'alerte"""
    level_classes = {
        'info': 'info',
        'attention': 'warning',
        'urgent': 'danger',
        'critique': 'dark',
    }
    return level_classes.get(level, 'secondary')

@register.filter
def section_color(section):
    """Retourne la couleur associée à une section"""
    section_colors = {
        'extrusion': 'primary',
        'imprimerie': 'info',
        'soudure': 'success',
        'recyclage': 'warning',
    }
    return section_colors.get(section, 'secondary')