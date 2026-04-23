import re
from django.template.loader import get_template


REGISTRY = dict()

def register(cls, model_cls=None):
    """
    Decorator to register a renderer class for a model class. When rendering
    pages or sections the registry will be checked for a renderer class. If a
    renderer class is found it will be used. Otherwise pages will be rendered
    using the PageRenderer and sections will be rendered using the
    SectionRenderer.
    """
    model_cls = model_cls or cls.model_cls
    REGISTRY[model_cls] = cls
    return cls


class BaseRenderer:
    """
    Base renderer class. This class provides the basic functionality to render a
    Page or Section instance using a template. It can be extended to add custom
    rendering logic or to use different templates. A child class can change the
    whole rendering logic as long as the `render` method returns valid HTML.
    """
    template_name = None
    base_type_name = None

    def __init__(self, obj):
        self.obj = obj

    def get_template_name(self):
        """
        Return the template to use for this model. If template_name is set it
        will be used. If not the template name will be the class name as snake
        case. Templates for pages will be looked up in a `pages` folder, and for
        sections in a `sections` folder.
        """
        if self.template_name:
            return self.template_name
        else:
            # Cast class name to snake case for the template file name.
            cls = self.obj.__class__
            template_name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
            return f'{self.base_type_name}s/{template_name}.html'

    def get_context(self, extra_context=None):
        """
        Return the context to use when rendering the template. By default the
        context will contain the object being rendered as `page` or `section`
        depending on the base type.
        """
        context = extra_context or {}
        context[self.base_type_name] = self.obj
        return context

    def render(self, extra_context=None):
        """
        Return the rendered HTML using `get_template_name` and `get_context`
        methods.
        """
        template = get_template(self.get_template_name())
        context = self.get_context(extra_context)
        return template.render(context)


class PageRenderer(BaseRenderer):
    """
    Renderer for Page instances.
    """
    base_type_name = 'page'


class SectionRenderer(BaseRenderer):
    """
    Renderer for Section instances.
    """
    base_type_name = 'section'
