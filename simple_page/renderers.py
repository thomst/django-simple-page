"""
To build the HTML for a page or section object a renderer class is used. While a
section renderer produces a html snippet representing the section object, a page
renderer provides a full html document - including all its sections.

Nevertheless, both renderer classes are based on the same concept, using the
proven triad of `get_template_name`, `get_context` and `render` methods.

While there are default renderers for pages and sections which do the obvious,
you can equip your page and section models with customized renderer classes.

Renderer classes using django's :class:`~django.forms.MediaDefiningClass` as
metaclass. They can be equipped with a `Media` class like django's forms and
widgets::

    from simple_page import renderers
    from .models import FancySection

    @renderers.register(FancySection)
    class FancySectionRenderer(renderers.SectionRenderer):
        class Media:
            css = dict(all=['fancy_section.css'])
            js = ['fancy_section.js']


It is the responsibility of the page renderer to merge the media definitions of
all renderers involved and provide them as a `media` template variable. For more
details see :meth:`~.PageRenderer.get_media_assets`.
"""

from django.template.loader import get_template
from django.template.context import Context
from django.forms.widgets import MediaDefiningClass
from .utils import camel_to_snake
from .models import Page


REGISTRY = dict()

def register(model_cls, renderer_cls=None, context=None):
    """
    Register a renderer class for a page or section model. This function can also be
    used as a decorator for your renderer class::

        @renderers.register(FancyPage)
        class FancyPageRenderer(renderers.PageRenderer):
            ...

    :class:`Section renderer <.SectionRenderer>` can be applied context
    specific. A context can be a page type, a region name or a tuple of page
    type and region name::

        @renderers.register(FancySection, context='main')
        class MainRegionFancySectionRenderer(renderers.SectionRenderer):
            ...

    or::

        @renderers.register(FancySection, context=(FancyPage, 'main'))
        class FancyPageMainRegionFancySectionRenderer(renderers.SectionRenderer):
            ...

    This allows you to use different renderers depending on where a section
    appears. See :func:`~.get_section_renderer` for more details about how a
    renderer will be choosen.

    :param model_cls: model to be rendered
    :type model_cls: :class:`~.models.Page` or :class:`~.models.Section`
    :param renderer_cls: renderer class
    :type renderer_cls: :class:`~.PageRenderer` or :class:`~.SectionRenderer`
    :param context: context where a section renderer should be applied
    :type context: :class:`~.models.Page` or str or tuple of both, optional
    """
    def _register(renderer_cls):
        if issubclass(model_cls, Page):
            REGISTRY[model_cls] = renderer_cls
        else:
            REGISTRY[model_cls] = REGISTRY.get(model_cls) or dict()
            REGISTRY[model_cls][context] = renderer_cls
        return renderer_cls

    # Usage as function.
    if renderer_cls:
        _register(renderer_cls)

    # Usage as decorator.
    else:
        return _register


def get_page_renderer(page):
    """
    Return the registered renderer for the page or :class:`~.PageRenderer`.

    :param page: page instance to be rendered
    :type page: :class:`~.models.Page`
    :return: renderer class
    :rtype: :class:`~.PageRenderer`
    """
    return REGISTRY.get(type(page), PageRenderer)


def get_section_renderer(section, page=None, region=None):
    """
    Return a renderer instance for the section.

    We look for a registered renderer in this order:

    * page-type and region specific
    * region specific
    * page-type specific
    * neither page-type nor region specific

    The first one found will be returned. Otherwise the
    :class:`~.SectionRenderer` is used as fallback.

    :param obj: section instance
    :type obj: :class:`~.models.Section`
    :param page: page the section will be rendered for
    :type page: :class:`~.models.Page`
    :param str region: region the section  will be rendered in
    :return: renderer class
    :rtype: :class:`~.SectionRenderer`
    """
    if type(section) in REGISTRY:
        # One of these keys must have been used to register a renderer class.
        for key in [(type(page), region), region, type(page), None]:
            if key in REGISTRY[type(section)]:
                return REGISTRY[type(section)][key]
    else:
        return SectionRenderer


class SectionRenderer(metaclass=MediaDefiningClass):
    """
    Renderer for Section instances. Section renderers will most likely be used
    from within the page's template using the builtin `include` tag::

        {% for section in regions.main.sections %}
            {% include section %}
        {% endfor %}

    This way the :meth:`~.render` method will be called and its output will be
    included in the page's template. By default the `include` tag will pass the
    current context to the section renderer. See the Django docs for the
    `include tag <https://docs.djangoproject.com/en/stable/ref/templates/builtins/#std-templatetag-include>`_

    Since a section renderer is initialized with the page, region and request,
    it knows about the full context in which a section should be rendererd.
    Customized renderer classes can use this information to adapt the rendering
    logic for a specific rendering context.

    :param section: section instance to be rendered
    :type section: :class:`~.models.Section`
    :param page: page the section will be rendered for
    :type page: :class:`~.models.Page`
    :param str region: region the section  will be rendered in
    :param request: HTTP request, optional
    :type request: :class:`~django.http.HttpRequest`, optional
    """
    def __init__(self, section, page, region, request=None):
        self.obj = section
        self.section = section
        self.page = page
        self.region = region
        self.request = request

    def get_template_name(self):
        """
        Return the template path. It will be build based on the section's class
        name:

        "sections/<section_class_name_in_snake_case>.html"
        """
        template_name = camel_to_snake(self.section.__class__.__name__)
        return f'sections/{template_name}.html'

    def get_context(self):
        """
        Build and return rendering context:

        - `section`: section object

        :return: rendering context
        :rtype: dict
        """
        return dict(section=self.section)

    def render(self, context=None):
        """
        Return the rendered HTML using the template and context returned by
        :meth:`~.get_template_name` and :meth:`~.get_context` methods.

        :param context: additional context to be passed to the template
        :type context: :class:`~django.template.Context`, optional
        :return: rendered HTML
        :rtype: str
        """
        template = get_template(self.get_template_name())
        context = context or Context()
        context.update(self.get_context())
        return template.render(context.flatten(), request=self.request)


class PageRenderer(metaclass=MediaDefiningClass):
    """
    Renderer for Page instances. This renderer will most likely be used in a
    view function. Simply call its :meth:`~.render` method and return its output
    as a HTTP response::

        def page_view(request, slug, **kwargs):
            page = get_object_or_404(Page, slug=slug).resolve_obj()
            renderer_cls = get_page_renderer(page)
            return HttpResponse(renderer_cls(page, request).render(**kwargs))

    You are free to pass the request to the renderer. If you do your template
    will be rendered with a :class:`~django.template.RequestContext`.

    :param page: page instance to be rendered
    :type page: :class:`~.models.Page`
    :param request: HTTP request, optional
    :type request: :class:`~django.http.HttpRequest`, optional
    """
    def __init__(self, page, request=None):
        self.page = page
        self.request = request

    def get_region_data(self, region, title):
        """
        Build and return a dictionary holding the region's data:

        - `name`: region name
        - `title`: region title
        - `sections`: list of section renderers for this region

        :param str region: region name
        :param str tilte: region title
        :return: region data holding title, name and sections for this region
        :rtype: dict
        """
        region_data = {'title': title, 'name': region, 'sections': []}
        for section in getattr(self.page, region):
            renderer_cls = get_section_renderer(section, self.page, region)
            renderer = renderer_cls(section, self.page, region, self.request)
            region_data['sections'].append(renderer)
        return region_data

    def get_media_assets(self, sections):
        """
        Merge media definitions of all renderers involved. The page's one and
        all its section renderers. Return the merged
        :class:`~django.forms.Media` object.

        :return: merged media assets
        :rtype: :class:`~django.forms.Media`
        """
        media = self.media
        for section in sections:
            media += section.media
        return media

    def get_template_name(self):
        """
        Return the template path. It will be build based on the page's class
        name:

        "pages/<page_class_name_in_snake_case>.html"
        """
        template_name = camel_to_snake(self.page.__class__.__name__)
        return f'pages/{template_name}.html'

    def get_context(self):
        """
        Build the rendering context variables:

        - `page`: page object
        - `sections`: list of all section renderers
        - `regions`: mapping of region names to their data build by
          :meth:`~.get_region_data`
        - `media`: media assets build by :meth:`~.get_media_assets`

        As a shortcut each region data will also be added using the region's
        name as an own context variable. In your template these variables are
        equivalent: `{{ regions.main }}` and `{{ main }}`.

        :return dict: rendering context
        """
        # Add regions, sections and media to the context.
        context = dict()
        context['page'] = self.page
        context['regions'] = dict()
        context['sections'] = list()
        for region, title in self.page.get_regions():
            context[region] = self.get_region_data(region, title)
            context['regions'][region] = context[region]
            context['sections'].extend(context[region]['sections'])
        context['media'] = self.get_media_assets(context['sections'])

        return context

    def render(self, **context):
        """
        Return the rendered HTML using the template and context returned by
        :meth:`~.get_template_name` and :meth:`~.get_context` methods.

        :param dict context: additional context to be passed to the template
        :return str: rendered HTML
        """
        template = get_template(self.get_template_name())
        context.update(self.get_context())
        return template.render(context, request=self.request)
