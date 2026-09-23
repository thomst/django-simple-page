from simple_page import renderers
from .models import PageWithHeader, TextSection, FooterSection


@renderers.register(PageWithHeader)
class PageWithHeaderRenderer(renderers.PageRenderer):
    class Media:
        css = dict(all=['pages/header.css'])


@renderers.register(TextSection)
class TextSectionRenderer(renderers.SectionRenderer):
    def get_context_data(self):
        context = super().get_context_data()
        context['title'] = self.section.title or f'{self.section.text[:8]} ...'
        return context


@renderers.register(FooterSection)
class FooterSectionRenderer(renderers.SectionRenderer):
    def get_context_data(self):
        context = super().get_context_data()
        context['title'] = self.section.title or f'{self.section.text[:8]} ...'
        context['text'] = f'{self.section.text[:80]} ...'
        return context
