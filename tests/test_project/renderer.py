from simple_page import renderer


class ExtraPageRenderer(renderer.PageRenderer):
    def get_context(self, extra_context=None):
        context = super().get_context(extra_context)
        context['special_info'] = self.obj.special_info
        return context


class TextSectionRenderer(renderer.SectionRenderer):
    template_name = 'sections/text_with_title_section.html'

    def get_context(self, extra_context=None):
        context = super().get_context(extra_context)
        context['title'] = f'{self.obj.text[:8]}...'
        return context
