from django import template

register = template.Library()

@register.filter
def currency_vn(value):
    try:
        value = int(value)
        return f"{value:,.0f} VNĐ".replace(",", ".")
    except (ValueError, TypeError):
        return value
