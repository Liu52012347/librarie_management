from django import template
from django.utils.safestring import mark_safe

register = template.Library()

STATUS_MAP = {
    0: ("warning", "待确认"),
    1: ("primary", "已确认"),
    2: ("purple", "就诊中"),
    3: ("success", "已完成"),
    4: ("secondary", "已取消"),
    5: ("danger", "爽约"),
}

@register.simple_tag
def status_badge(status):
    info = STATUS_MAP.get(status, ("secondary", "未知"))
    color = info[0]
    if color == "purple":
        return mark_safe(f'<span class="badge" style="background-color:#6f42c1;">{info[1]}</span>')
    return mark_safe(f'<span class="badge bg-{color}">{info[1]}</span>')

@register.simple_tag
def status_color(status):
    info = STATUS_MAP.get(status, ("secondary", "未知"))
    colors = {"warning": "#ffc107", "primary": "#0d6efd", "success": "#198754", "secondary": "#6c757d", "danger": "#dc3545"}
    if status == 2:
        return "#6f42c1"
    return colors.get(info[0], "#6c757d")


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)