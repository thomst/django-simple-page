from django import template

register = template.Library()


@register.inclusion_tag("simple_page/menu.html")
def menu(page, max_level=None, include_root=False):
    context = dict()
    context['page'] = page
    context['max_level'] = max_level
    context['nodes'] = page.get_root().get_descendants(include_self=include_root)
    return context


@register.filter
def is_active(page, node):
    root = page.get_root()
    ancestors = page.get_ancestors(include_self=True)
    return (
        node in ancestors and node != root
        or page == root and node == root
    )


@register.filter
def level(node):
    return node.get_ancestors(include_self=True).count()
