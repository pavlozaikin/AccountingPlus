from __future__ import annotations

from django import template


register = template.Library()


@register.filter
def get_item(mapping: dict, key: str):
    if mapping is None:
        return ""
    return mapping.get(str(key), "")
