from django import template

register = template.Library()


@register.inclusion_tag("simple_page/menu.html")
def menu(page, max_level=None, include_root=False):
    """
    An inclusion tag to generate a tree based menu using nested lists. The
    current page and its ancestors will be marked as active by a css class
    "active". Each menu list will have a css class "nav-level-x" where x is the
    level of the menu starting with 1.

    :param page: current page
    :type page: :class:`~.models.Page`
    :param int max_level: maximum level of submenus, defaults to None
    :param bool include_root: whether to include the root page, defaults to False
    :return dict: the context for the menu template
    """
    context = dict()
    context['page'] = page
    context['max_level'] = max_level
    context['nodes'] = page.get_root().get_descendants()
    if include_root:
        context['root'] = page.get_root()
    return context


@register.filter
def is_active(page, node):
    """
    Filter tag returning True for the current page and its ancestors. False
    otherwise.

    :param page: current page
    :type page: :class:`~.models.Page`
    :param node: the page node to check
    :type node: :class:`~.models.Page`
    :return bool: True if the node is active, False otherwise
    """
    ancestors = page.get_ancestors(include_self=True)
    return node in ancestors


@register.filter
def level(node):
    """
    Filter tag returning the level of the page node starting with 1.

    :param node: the page node
    :type node: :class:`~.models.Page`
    :return int: the level of the page node
    """
    return node.get_ancestors(include_self=True).count()
