from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse
from .models import Page
from .renderers import get_renderer


def page_view(request, slug=None, **kwargs):
    """
    Simple view function for pages. Get the page, find the right renderer for it
    and return a HTTP response with the rendered page. The page is either
    choosen by its slug or if no slug is given the root page is used.

    :param request: HTTP request
    :type request: :class:`~django.http.HttpRequest`
    :param str slug: slug of the page to be rendered
    :param dict kwargs: Additional data as keyword arguments
    :return: HTTP response with the rendered page
    :rtype: :class:`~django.http.HttpResponse`
    :raises Http404: if no page could be found
    """
    # Get page by slug.
    if slug:
        page = get_object_or_404(Page, slug=slug).resolved_obj

    # Or get the root page if no slug is given.
    else:
        try:
            page = Page.objects.filter(parent=None).first().resolved_obj
            assert page is not None
        except AssertionError:
            raise Http404("No root page found.")

    renderer_cls = get_renderer(page)
    return HttpResponse(renderer_cls(page, request, **kwargs).render())
