from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Page
from .renderer import REGISTRY, PageRenderer


def page(request, slug):
    """
    View function to render a page by its slug.
    """
    page = get_object_or_404(Page, slug=slug)
    page = page.resolve_obj()
    renderer_cls = REGISTRY.get(type(page), PageRenderer)
    renderer = renderer_cls(page)
    return HttpResponse(renderer.render(request))
