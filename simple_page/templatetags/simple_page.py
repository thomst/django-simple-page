from django import template

register = template.Library()


@register.inclusion_tag("simple_page/menu.html")
def menu(page, max_level=None):
    context = dict()
    context['page'] = page
    context['nodes'] = page.get_root().get_descendants()
    context['max_level'] = max_level
    return context


@register.filter
def is_active(page, node):
    ancestors = page.get_ancestors(include_self=True)
    return node in ancestors


@register.filter
def level(node):
    return node.get_ancestors(include_self=True).count()
