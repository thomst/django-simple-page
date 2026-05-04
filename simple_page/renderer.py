import re
from django.template.loader import get_template
from .assets import get_assets
from .models import Page


REGISTRY = dict()

def register(renderer_cls, model_cls=None, context=None):
    """
    Register an :class:`~.Renderer` class for a page or section model. This
    function can also be used as a decorator for your model class::

        @renderer.register(FancyPageRenderer)
        class FancyPage(Page):
            ...

    For :class:`~.simple_page.models.Section` classes it is possible to define a
    context in which a renderer should be used. A context can be a page type, a
    region name or a tuple of page typen and region name. You can register
    multiple renderer classes with different contexts for a section::

        @renderer.register(MainSectionRenderer, context='main')
        @renderer.register(FancySectionRenderer, context=(FancyPage, 'main'))
        class FancySection(Section):
            ...

    In this example the `FancySectionRenderer` will be used when the section
    appears on a `FancyPage` in a 'main' region. The `MainSectionRenderer` will
    be used for all 'main' regions on all other pages. And in all other contexts
    :class:`~.SectionRenderer` will be used. See also
    :func:`~.get_section_renderer`.

    :param renderere_cls: the renderer class to be registered
    :type renderer_cls: :class:`~.Renderer`
    :param model_cls: the model for which the renderer should be used
    :type model_cls: :class:`~simple_page.models.Page` or :class:`~simple_page.models.Section`
    :param context: a context in which a section should be rendered with the renderer class
    :type context: :class:`~simple_page.models.Page` or str or tuple
    """
    def _register(model_cls):
        if issubclass(model_cls, Page):
            REGISTRY[model_cls] = renderer_cls
        else:
            REGISTRY[model_cls] = REGISTRY.get(model_cls) or dict()
            REGISTRY[model_cls][context] = renderer_cls
        return model_cls

    # Usage as function.
    if model_cls:
        _register(model_cls)

    # Usage as decorator.
    else:
        return _register


def get_page_renderer(page):
    """
    Return the registered renderer for the page or :class:`~.PageRenderer`.

    :param page: page instance to be rendered
    :type page: :class:`~simple_page.models.Page`
    :return: renderer class
    :rtype: :class:`~.PageRenderer`
    """
    return REGISTRY.get(type(page), PageRenderer)


def get_section_renderer(section, page=None, region=None):
    """
    Return a renderer instance for the section.

    We look for a registered renderer in this order:

    * page-type and region specific
    * only region specific
    * only page-type specific
    * not page-type and region specific

    The first one found will be returned. Otherwise the
    :class:`~.SectionRenderer` is used as fallback.

    :param obj: section instance
    :type obj: :class:`~.simple_page.models.Section`
    :param page: page the section will be rendered for
    :type page: :class:`~.simple_page.models.Page`
    :param str region: region the section  will be rendered in
    :return: renderer class
    :rtype: :class:`~.SectionRenderer`
    """
    if type(section) in REGISTRY:
        keys = [
            (type(page), region),
            region,
            type(page),
            None,
        ]
        for key in keys:
            if key in REGISTRY[type(section)]:
                return REGISTRY[type(section)][key]
    else:
        return SectionRenderer


class Renderer:
    """
    Base renderer class. This class provides the basic functionality to render a
    Page or Section instance. It uses the proven triad of `get_template_name`,
    `get_context` and `render` methods. But can be customized to any extend. All
    a child class has to provide is a `render` method returning valid HTML.
    """
    template_name = None

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
        Return the context to use when rendering the template. By default the
        context will contain the object being rendered as 'page' or 'section' -
        depending on the object's type.
        """
        context = self.kwargs.get('extra_context', dict())
        obj_type = 'page' if isinstance(self.obj, Page) else 'section'
        context[obj_type] = self.obj
        return context

    def render(self):
        """
        Return the rendered HTML using the template and context returned by
        :meth:`~.get_template_name` and :meth:`~.get_context` methods.
        """
        template = get_template(self.get_template_name())
        context = self.get_context()
        return template.render(context)


class SectionRenderer(Renderer):
    """
    Renderer for Section instances.
    """


class PageRenderer(Renderer):
    """
    Renderer for Page instances.
    """

    def render_section(self, section, region):
        """
        Return a section rendered as html.
        """
        renderer_cls = get_section_renderer(section, self.obj, region)
        renderer = renderer_cls(section, self.request, **self.kwargs)
        return renderer.render()

    def get_section_data(self, section, region):
        """
        Return a dictonary holding the section as object and as rendered html
        using 'obj' and 'html' as keys.
        """
        return dict(
            obj=section,
            html=self.render_section(section, region)
        )

    def get_region_data(self, name, title):
        """
        Return a dictonary with the name, the title and the sections of a
        region. The sections will be a dictonary of the section object and its
        rendered html. See :meth:`~.get_section_data`.
        """
        region = {'title': title, 'name': name, 'sections': []}
        for section in getattr(self.obj, name):
            section_data = self.get_section_data(section, name)
            region['sections'].append(section_data)
        return region

    def get_assets(self):
        """
        Return an :class:`~.simple_page.assets.Assets` instance which holding
        all the assets from the page and its sections.
        """
        media = get_assets(self.obj)
        for section in self.obj.sections.select_subclasses():
            media += get_assets(section)
        return media

    def get_context(self):
        """
        Add regions and media assets to the context.

        Regions will be added as template variables on their own and as a list
        named 'regions'. Each region is a dictonary of its name, title and its
        sections. See :meth:`~.get_region_data`.

        Media assets will be the merged assets of the page and all its sections.
        See :meth:`~.get_assets`.
        """
        context = super().get_context()

        # Add regions to the context.
        context['regions'] = []
        for name, title in self.obj.get_regions():
            context[name] = self.get_region_data(name, title)
            context['regions'].append(context[name])

        # Add media to the context.
        context['media'] = self.get_assets()

        return context
