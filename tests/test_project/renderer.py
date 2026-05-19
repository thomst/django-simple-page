from simple_page import renderer


class PageWithHeaderRenderer(renderer.PageRenderer):
    class Media:
        css = dict(all=['pages/header.css'])

    def get_context(self):
        context = super().get_context()
        context['header_info'] = self.obj.header_info
        return context
