from simple_page import renderer


class MainPageRenderer(renderer.PageRenderer):
    class Media:
        css = dict(all=['pages/base.css'])


class ExtraPageRenderer(renderer.PageRenderer):
    class Media:
        css = {
            'all': ['test_project/extra_page.css']
        }
        js = ['test_project/extra_page.js']

    def get_context(self):
        context = super().get_context()
        context['special_info'] = self.obj.special_info
        return context


class TextSectionRenderer(renderer.SectionRenderer):
    template_name = 'sections/text_with_title_section.html'

    class Media:
        css = {
            'all': ['test_project/text_section.css']
        }
        js = ['test_project/text_section.js']

    def get_context(self):
        context = super().get_context()
        context['title'] = f'{self.obj.text[:8]}...'
        return context


class ExtraSectionRenderer(renderer.SectionRenderer):
    template_name = 'sections/extra_text_section.html'
    extra_title = 'Extra Title'

    def get_context(self):
        context = super().get_context()
        context['extra_title'] = f'{{ self.extra_title }}: {self.obj.text[:8]}...'
        return context
