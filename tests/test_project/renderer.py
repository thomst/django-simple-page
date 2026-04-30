from simple_page import renderer


class ExtraPageRenderer(renderer.PageRenderer):
    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['special_info'] = self.obj.special_info
        return context


class TextSectionRenderer(renderer.SectionRenderer):
    template_name = 'sections/text_with_title_section.html'

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['title'] = f'{self.obj.text[:8]}...'
        return context
