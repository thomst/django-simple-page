from django.forms import Media


REGISTRY = dict()

def register(assets_cls, model_cls=None):
    """
    Decorator to register an asset class for a page or section model. When
    rendering pages or sections the registry will be checked for assets.
    """
    def _register(model_cls):
        REGISTRY[model_cls] = assets_cls
        return model_cls

    if model_cls:
        _register(model_cls)
    else:
        return _register


def get_assets(obj):
    """
    Return an assets instance for the object. Check for a registered assets
    class. Use :class:`~.Assets` as a fallback.
    """
    return REGISTRY.get(type(obj), Assets)()


class Assets(Media):
    """
    Base class to manage JavaScript and CSS assets for pages and sections. Use
    this class to define js and css attributes as you would do in a django form
    `Media` classes.
    """
    def __init__(self):
        css = getattr(self, 'css', {})
        js = getattr(self, 'js', [])
        super().__init__(css=css, js=js)
