from simple_page import renderers
from .models import PageWithHeader, TextSection


@renderers.register(PageWithHeader)
class PageWithHeaderRenderer(renderers.PageRenderer):
    class Media:
        css = dict(all=['pages/header.css'])

    def get_context(self):
        context = super().get_context()
        context['header_info'] = self.obj.header_info
        return context


@renderers.register(TextSection)
class TextSectionRenderer(renderers.SectionRenderer):
    def get_context(self):
        context = super().get_context()
        context['title'] = self.obj.title or f'{self.obj.text[:8]} ...'
        context['text'] = self.obj.text
        return context


@renderers.register(TextSection, context='footer')
class FooterTextSectionRenderer(renderers.SectionRenderer):
    def get_context(self):
        context = super().get_context()
        context['text'] = f'{self.obj.text[:80]} ...'
        return context
