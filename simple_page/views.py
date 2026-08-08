from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Page
from .renderers import get_page_renderer


def page_view(request, slug, **kwargs):
    """
    Simple view function for pages. Get the page by its slug, find the right
    renderer for it and return a HTTP response with the rendered page.

    :param request: HTTP request
    :type request: :class:`~django.http.HttpRequest`
    :param str slug: slug of the page to be rendered
    :param kwargs: Additional data as keyword arguments (default empty dict)
    :return: HTTP response with the rendered page
    :rtype: :class:`~django.http.HttpResponse`
    :raises Http404: if no page with the given slug exists
    """
    page = get_object_or_404(Page, slug=slug).resolve_obj()
    renderer_cls = get_page_renderer(page)
    return HttpResponse(renderer_cls(page, request).render(**kwargs))
