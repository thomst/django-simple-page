from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Page


def page(request, slug=None):
    """
    View function to render a page by its slug.
    """
    page = get_object_or_404(Page, slug=slug or 'home')
    page = page.resolve_obj()
    return HttpResponse(page.html)
