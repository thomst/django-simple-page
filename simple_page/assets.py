from django.forms import Media
from .models import Page


REGISTRY = dict()

def register(assets_cls, model_cls=None, context=None):
    """
    Register an :class:`~.Assets` class for a page or section model. This
    function can also be used as a decorator for the model class::

        @assets.register(FancySectionAssets):
        class FancySection(Section):
            ...
    """
    def _register(model_cls):
        if issubclass(model_cls, Page):
            REGISTRY[model_cls] = assets_cls
        else:
            REGISTRY[model_cls] = REGISTRY.get(model_cls) or dict()
            REGISTRY[model_cls][context] = assets_cls
        return model_cls

    if model_cls:
        _register(model_cls)
    else:
        return _register


def get_page_assets(page):
    """
    Return an assets instance for the page. Check for a registered assets
    class. Use :class:`~.Assets` as a fallback.
    """
    return REGISTRY.get(type(page), Assets)


def get_section_assets(section, page=None, region=None):
    """
    Return a assets instance for the section.

    We look for a registered assets in this order:

    * page-type and region specific
    * region specific
    * page-type specific
    * neither page-type nor region specific

    The first one found will be returned. Otherwise the
    :class:`~.Assets` is used as fallback.

    :param obj: section instance
    :type obj: :class:`~.simple_page.models.Section`
    :param page: page the section will be rendered for
    :type page: :class:`~.simple_page.models.Page`
    :param str region: region the section  will be rendered in
    :return: assets class
    :rtype: :class:`~.Assets`
    """
    if type(section) in REGISTRY:
        # One of these keys must have been used to register a assets class.
        for key in [(type(page), region), region, type(page), None]:
            if key in REGISTRY[type(section)]:
                return REGISTRY[type(section)][key]
    else:
        return Assets


class Assets(Media):
    """
    Base class for css and javascript media definitions. It works exactly as the
    `Media` class for django forms: Simply set the css and js class attributes
    and register your Assets for your pages or sections.
    """
    def __init__(self):
        css = getattr(self, 'css', {})
        js = getattr(self, 'js', [])
        super().__init__(css=css, js=js)
