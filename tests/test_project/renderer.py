from simple_page import renderer


class ExtraPageRenderer(renderer.PageRenderer):
    class Media:
        css = dict(all=['pages/extra.css'])

    def get_context(self):
        context = super().get_context()
        context['special_info'] = self.obj.special_info
        return context
