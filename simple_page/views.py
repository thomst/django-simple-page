from django.shortcuts import render, get_object_or_404

from .models import Page


def page(request, slug=None):
    """
    View function to render a page by its slug.
    """
    page = get_object_or_404(Page, slug=slug or 'home')
    template = page.get_template()
    return render(request, template, {'page': page})
