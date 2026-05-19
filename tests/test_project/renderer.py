from simple_page import renderer
from.models import PageWithHeader, TextSection


@renderer.register(PageWithHeader)
class PageWithHeaderRenderer(renderer.PageRenderer):
    class Media:
        css = dict(all=['pages/header.css'])

    def get_context(self):
        context = super().get_context()
        context['header_info'] = self.obj.header_info
        return context


@renderer.register(TextSection)
class TextSectionRenderer(renderer.SectionRenderer):
    def get_context(self):
        context = super().get_context()
        context['title'] = self.obj.title or f'{self.obj.text[:8]} ...'
        context['text'] = self.obj.text
        return context


@renderer.register(TextSection, context='footer')
class FooterTextSectionRenderer(renderer.SectionRenderer):
    def get_context(self):
        context = super().get_context()
        context['text'] = f'{self.obj.text[:80]} ...'
        return context
