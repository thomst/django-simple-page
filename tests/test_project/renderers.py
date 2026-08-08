from simple_page import renderers
from .models import PageWithHeader, TextSection


@renderers.register(PageWithHeader)
class PageWithHeaderRenderer(renderers.PageRenderer):
    class Media:
        css = dict(all=['pages/header.css'])

    def get_context(self):
        context = super().get_context()
        context['header_info'] = self.page.header_info
        return context


@renderers.register(TextSection)
class TextSectionRenderer(renderers.SectionRenderer):
    def get_context(self):
        context = super().get_context()
        if self.region == 'footer':
            context['text'] = f'{self.section.text[:80]} ...'
        else:
            context['title'] = self.section.title or f'{self.section.text[:8]} ...'
            context['text'] = self.section.text
        return context
