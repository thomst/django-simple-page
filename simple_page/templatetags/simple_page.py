from django import template
from ..renderer import REGISTRY, SectionRenderer


register = template.Library()


@register.simple_tag
def section_html(section):
    """
    Return the rendered HTML of a section as a string.

    Usage: {% section_html section_object %}
    """
    renderer_cls = REGISTRY.get(type(section), SectionRenderer)
    return renderer_cls(section).render()


@register.simple_tag(takes_context=True)
def section_html_with_context(context, section):
    """
    Return the rendered HTML of a section as a string.
    Passes the template context as extra context to the renderer.

    Usage: {% section_html_with_context section_object %}
    """
    renderer_cls = REGISTRY.get(type(section), SectionRenderer)
    return renderer_cls(section).render(extra_context=context)
