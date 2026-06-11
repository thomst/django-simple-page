"""
To build HTML for a page or section object a renderer class is used. While a
section renderer produces a html snippet representing the section object, a page
renderer provides a full html document for a page. Including all its sections.

Nevertheless, both renderers are based on the same concept, using the proven
triad of `get_template_name`, `get_context` and `render` methods.

There is a default renderer for pages as well as for sections. Which are
probably sufficient for most use cases. Still you are free to write your own
renderer classes and :func:`~.register` them for your page and section models.
The only thing a renderer class has to provide is a `render` method returning
valid HTML.

Renderer classes using django's :class:`~django.forms.MediaDefiningClass` as
metaclass. They can be equipped with a `Media` classes like django's forms and
widgets::

.. code-block:: python

    from simple_page import renderers

    class FancySectionRenderer(renderers.SectionRenderer):
        class Media:
            css = dict(all=['fancy_section.css'])
            js = ['fancy_section.js']


It is the responsibility of the page renderer to merge the media
definitions of all renderers involved and provide them as a `media` template
variable. For more details see :meth:`~.PageRenderer.get_media_assets`.
"""

import re
from django.template.loader import get_template
from django.forms.widgets import MediaDefiningClass
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
        class
        FancyPageMainRegionFancySectionRenderer(renderers.SectionRenderer):
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
        return model_cls

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


class BaseRenderer(metaclass=MediaDefiningClass):
    """
    Base renderer class.
    """

    template_name = None
    """
    Template name. Default is None. See :meth:`~.get_template_name`.
    """

    def __init__(self, obj, request=None, **kwargs):
        """
        Initialize the renderer.

        :param obj: object to be rendered
        :type obj: :class:`~.models.Page` or :class:`~.models.Section`
        :param request: request object (default: None)
        :type request: :class:`~django.http.HttpRequest`
        :param kwargs: Additional data as keyword arguments (default: dict())
        """
        self.obj = obj
        self.request = request
        self.kwargs = kwargs

    def render(self):
        """
        Return the rendered HTML using the template and context returned by
        :meth:`~.get_template_name` and :meth:`~.get_context` methods.
        """
        template = get_template(self.get_template_name())
        context = self.get_context()
        return template.render(context)


class SectionRenderer(BaseRenderer):
    """
    Renderer for Section instances.
    """
    # TODO: Use a get_template method instead.
    def get_template_name(self):
        """
        Return template name. If :attr:`~.template_name` is set it will be
        returned. Otherwise the template name will be constructed as follows:

        "sections/<section_class_name_in_snake_case>.html"
        """
        if self.template_name:
            return self.template_name
        else:
            cls_name = self.obj.__class__.__name__
            template_name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls_name).lower()
            return f'sections/{template_name}.html'

    def get_context(self):
        """
        Build and return rendering context:

        - `section`: section object

        :return: rendering context
        :rtype: dict
        """
        context = self.kwargs.get('extra_context', dict())
        context['section'] = self.obj
        return context


class PageRenderer(BaseRenderer):
    """
    Renderer for Page instances.
    """
    def get_template_name(self):
        """
        Return template name. If :attr:`~.template_name` is set it will be
        returned. Otherwise the template name will be constructed as follows:

        "pages/<page_class_name_in_snake_case>.html"
        """
        if self.template_name:
            return self.template_name
        else:
            cls_name = self.obj.__class__.__name__
            template_name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls_name).lower()
            return f'pages/{template_name}.html'

    def get_section_data(self, section, region):
        """
        Build and return a dictionary holding the section's data:

        - `obj`: section object itself
        - `renderer`: renderer object for this section
        - `html`: section's html build by the renderer returned by
          :func:`~.get_section_renderer`

        :param section: section object
        :type section: :class:`~.models.Section`
        :param str region: region name
        :return: section data holding the section object and the rendered html
        :rtype: dict
        """
        renderer_cls = get_section_renderer(section, self.obj, region)
        renderer = renderer_cls(section, self.request, **self.kwargs)
        return dict(
            obj=section,
            renderer=renderer,
            html=renderer.render(),
        )

    def get_region_data(self, region, title):
        """
        Build and return a dictionary holding the region's data:

        - `name`: region name
        - `title`: region title
        - `sections`: list of section data build by :meth:`~.get_section_data`

        :param str region: region name
        :param str tilte: region title
        :return: region data holding title, name and sections for this region
        :rtype: dict
        """
        region_data = {'title': title, 'name': region, 'sections': []}
        for section in getattr(self.obj, region):
            section_data = self.get_section_data(section, region)
            region_data['sections'].append(section_data)
        return region_data

    def get_media_assets(self, context):
        """
        Merge media definitions of the page's and all sections' renderers.
        Return them as string.

        :return str: merged media assets
        """
        media = self.media
        for region_data in context['regions'].values():
            for section_data in region_data['sections']:
                media += section_data['renderer'].media
        return str(media)

    def get_context(self):
        """
        Build rendering context:

        - `page`: page object
        - `media`: media assets build by :meth:`~.get_media_assets`
        - `regions`: mapping of region names to their data build by
          :meth:`~.get_region_data`

        As a shortcut each region data will also be added using the region's
        name as an own context variable.

        :return: rendering context
        :rtype: dict
        """
        # Add regions, sections and media to the context.
        context = self.kwargs.get('extra_context', dict())
        context['page'] = self.obj
        context['regions'] = dict()
        for region, title in self.obj.get_regions():
            context[region] = self.get_region_data(region, title)
            context['regions'][region] = context[region]
        context['media'] = self.get_media_assets(context)

        return context
