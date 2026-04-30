import re
from django.template.loader import get_template
from .assets import get_assets
from .models import Page


REGISTRY = dict()

def register(renderer_cls, model_cls=None):
    """
    Register an :class:`~.Renderer` class for a page or section model. This
    function can also be used as a decorator for your model class::

        @renderer.register(FancySectionRenderer):
        class FancySection(Section):
            ...
    """
    def _register(model_cls):
        REGISTRY[model_cls] = renderer_cls
        return model_cls

    if model_cls:
        _register(model_cls)
    else:
        return _register


def get_renderer(obj):
    """
    Return a renderer instance for the object. Check for a registered renderer
    class. Use the :class:`~.PageRenderer` or the :class:`~.SectionRenderer`
    instead - depending on the object's type.
    """
    default_renderer = PageRenderer if isinstance(obj, Page) else SectionRenderer
    return REGISTRY.get(type(obj), default_renderer)(obj)


class Renderer:
    """
    Base renderer class. This class provides the basic functionality to render a
    Page or Section instance. It uses the proven triad of `get_template_name`,
    `get_context` and `render` methods. But can be customized to any extend. All
    a child class has to provide is a `render` method returning valid HTML.
    """
    template_name = None

    def __init__(self, obj):
        self.obj = obj

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

    def get_context(self, *args, **kwargs):
        """
        Return the context to use when rendering the template. By default the
        context will contain the object being rendered as 'page' or 'section' -
        depending on the object's type.
        """
        context = kwargs.get('extra_context', dict())
        obj_type = 'page' if isinstance(self.obj, Page) else 'section'
        context[obj_type] = self.obj
        return context

    def render(self, *args, **kwargs):
        """
        Return the rendered HTML using the template and context returned by
        :meth:`~.get_template_name` and :meth:`~.get_context` methods.
        """
        template = get_template(self.get_template_name())
        context = self.get_context(*args, **kwargs)
        return template.render(context)


class SectionRenderer(Renderer):
    """
    Renderer for Section instances.
    """


class PageRenderer(Renderer):
    """
    Renderer for Page instances.
    """
    def get_context(self, *args, **kwargs):
        """
        Add regions, sections and media assets to the context.

        Regions will be added as list as 'regions' and as template variables on
        their own using their slug. Each region is a dictonary with 'title',
        'slug' and 'sections'.

        Sections will be a dictonary as well with the section object as 'obj'
        and the rendered HTML as 'html'.

        All registered media assets of the page and their sections will be
        merged and added as 'media' template variable.
        """
        context = super().get_context(*args, **kwargs)

        # Add regions with their title, id and sections to the context. The
        # regions will be available as list as well es template var of their
        # own. Sections will be a dictonary holding the section object as 'obj'
        # and the rendered HTML as 'html'.
        context['regions'] = []
        for region, title in self.obj.get_regions():
            context[region] = {'title': title, 'slug': region, 'sections': []}
            sections = getattr(self.obj, region)
            for section in sections:
                rendered_section = get_renderer(section).render(*args, **kwargs)
                section_data = {'obj': section, 'html': rendered_section}
                context[region]['sections'].append(section_data)
            context['regions'].append(context[region])

        # Add media assets to the context. Merging registered assets of the page
        # and all sections.
        context['media'] = get_assets(self.obj)
        for section in self.obj.sections.select_subclasses():
            context['media'] += get_assets(section)

        return context
