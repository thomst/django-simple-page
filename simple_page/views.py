from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Page
from .renderer import get_page_renderer


def page_view(request, slug, **kwargs):
    """
    View function to render a page by its slug.
    """
    page = get_object_or_404(Page, slug=slug).resolve_obj()
    renderer_cls = get_page_renderer(page)
    return HttpResponse(renderer_cls(page, request, **kwargs).render())
