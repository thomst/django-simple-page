import re
from django.template.loader import get_template
from django.forms.widgets import MediaDefiningClass
from .models import Page


REGISTRY = dict()

def register(model_cls, renderer_cls=None, context=None):
    """
    Register a :class:`renderer class <.BaseRenderer>` for a page or section
    model. This function can also be used as a decorator for your renderer
    class::

        @renderer.register(FancyPage)
        class FancyPageRenderer(PageRenderer):
            ...

    :class:`Section renderer <.SectionRenderer>` can be applied context
    specific. A context can be a page type, a region name or a tuple of page
    type and region name::

        @renderer.register(FancySection, context='main')
        class MainRegionFancySectionRenderer(SectionRenderer):
            ...

    or::

        @renderer.register(FancySection, context=(FancyPage, 'main'))
        class FancyPageMainRegionFancySectionRenderer(SectionRenderer):
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
    Base renderer class. This class provides the basic functionality to render a
    Page or Section instance. It uses the proven triad of `get_template_name`,
    `get_context` and `render` methods. But can be customized to any extend.
    Everything a child class has to provide is a `render` method returning valid
    HTML.

    Renderer classes using django's :class:`~django.forms.MediaDefiningClass` as
    metaclass. They can be equipped with `Media` classes as you know from django
    forms and widgets. Those media assets will be merged by a page renderer and
    provided as a 'media' template variable.

    :param obj: object to be rendered
    :type obj: :class:`~.models.Page` or :class:`~.models.Section`
    :param request: request object (default: None)
    :type request: :class:`~django.http.HttpRequest`
    :param kwargs: Additional data as keyword arguments (default empty dict)
    """

    template_name = None
    """
    Name of the template to be used for rendering. See :meth:`~.get_template_name`.
    """


    def __init__(self, obj, request=None, **kwargs):
        self.obj = obj
        self.request = request
        self.kwargs = kwargs

    def get_template_name(self):
        """
        Return the name of the template. If :attr:`~.template_name` is set it
        will be returned. Otherwise the template name will be constructed as
        follows:

        - Using 'pages' or 'sections' as folder - depending on the object's type.
        - And converting the object's class name to snake case with a html
          suffix as file name.

        For example the template name for a MyTextSection class would be
        `'sections/my_text_section.html'`.
        """
        if self.template_name:
            return self.template_name
        else:
            cls_name = self.obj.__class__.__name__
            template_name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls_name).lower()
            folder = 'pages' if isinstance(self.obj, Page) else 'sections'
            return f'{folder}/{template_name}.html'

    def get_context(self):
        """
        Build and return rendering context. Just a dict with the section or page
        object.

        :return: rendering context
        :rtype: dict
        """
        context = self.kwargs.get('extra_context', dict())
        key = 'page' if isinstance(self.obj, Page) else 'section'
        context[key] = self.obj
        return context

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



class PageRenderer(BaseRenderer):
    """
    Renderer for Page instances.
    """

    def get_section_data(self, section, region):
        """
        Return a dictonary holding the section as `obj` and its rendered html as
        `html`.

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
            html=renderer.render()
        )

    def get_region_data(self, region, title):
        """
        Return a dictonary with the `name`, the `title` and the `sections` of a
        region. `sections` will be a dictonary build by
        :meth:`~.get_section_data`.

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

    def get_media_assets(self):
        """
        Merge all media objects of the page and the sections renderers. Return
        them as string.

        :return str: merged media assets
        """
        media = get_page_renderer(self.obj)(self.obj).media
        for region, _ in self.obj.get_regions():
            for section in getattr(self.obj, region):
                section_renderer = get_section_renderer(section, self.obj, region)
                media += section_renderer(section).media
        return str(media)

    def get_context(self):
        """
        Add regions and media assets to the context.

        `regions` will be a dictonary mapping the regions slug name to the
        regions data build by :meth:`~.get_media_assets`. As a shortcut earch
        region data will be also added with its slug name as its own template
        variable.

        `media` will be the merged media assets from all renderers being
        involved as string. See :meth:`~.get_media_assets`.

        :return: rendering context
        :rtype: dict
        """
        # Add regions, sections and media to the context.
        context = super().get_context()
        context['media'] = self.get_media_assets()
        context['regions'] = dict()
        for region, title in self.obj.get_regions():
            context[region] = self.get_region_data(region, title)
            context['regions'][region] = context[region]

        return context
