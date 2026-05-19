from django import template

register = template.Library()


@register.inclusion_tag("simple_page/menu.html")
def menu(page, max_level=None, include_root=False):
    context = dict()
    context['page'] = page
    context['max_level'] = max_level
    context['nodes'] = page.get_root().get_descendants()
    if include_root:
        context['root'] = page.get_root()
    return context


@register.filter
def is_active(page, node):
    ancestors = page.get_ancestors(include_self=True)
    return node in ancestors


@register.filter
def level(node):
    return node.get_ancestors(include_self=True).count()
