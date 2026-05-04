from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from simple_page.models import Page, PageSection, Section
from simple_page import renderer
from simple_page.renderer import REGISTRY as RENDERER_REGISTRY
from simple_page.renderer import get_page_renderer, get_section_renderer
from simple_page.assets import REGISTRY as ASSETS_REGISTRY

from .models import TextSection, TextWithTitleSection, MainPage, ExtraPage
from .renderer import TextSectionRenderer, ExtraPageRenderer
from .assets import TextSectionAssets, ExtraPageAssets


class TestDataMixin:
    fixtures = ['testdata.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Fix the page_type references. The ids in the page fixtures might not
        # fit to the real content type ids.
        extra_pages = ExtraPage.objects.all()
        extra_page_type = ContentType.objects.get(model='extrapage')
        main_pages = Page.objects.exclude(id__in=[p.id for p in extra_pages])
        main_page_type = ContentType.objects.get(model='mainpage')
        for page in extra_pages:
            page.page_type = extra_page_type
            page.save()
        for page in main_pages:
            page.page_type = main_page_type
            page.save()


class RendererTests(TestDataMixin, TestCase):
    def test_page_renderer_registry(self):
        page = MainPage.objects.all()[0]
        renderer_cls = type('TestPageRenderer', (renderer.PageRenderer,), dict())
        renderer.register(renderer_cls, MainPage)
        self.assertEqual(renderer_cls, renderer.get_page_renderer(page))

    def test_section_renderer_register(self):
        section = TextSection.objects.all()[0]
        main_page = MainPage.objects.all()[0]
        extra_page = ExtraPage.objects.all()[0]

        # Register renderer classes for TextSection.
        renderer_cls_one = type('TestSectionOneRenderer', (renderer.SectionRenderer,), dict())
        renderer_cls_two = type('TestSectionTwoRenderer', (renderer.SectionRenderer,), dict())
        renderer_cls_three = type('TestSectionThreeRenderer', (renderer.SectionRenderer,), dict())
        renderer_cls_four = type('TestSectionFourRenderer', (renderer.SectionRenderer,), dict())
        renderer.register(renderer_cls_one, TextSection, context=(MainPage, 'main'))
        renderer.register(renderer_cls_two, TextSection, context='footer')
        renderer.register(renderer_cls_three, TextSection, context=MainPage)
        renderer.register(renderer_cls_four, TextSection)

        # Check the get_section_renderer function.
        self.assertEqual(renderer_cls_one, renderer.get_section_renderer(section, main_page, 'main'))
        self.assertEqual(renderer_cls_two, renderer.get_section_renderer(section, main_page, 'footer'))
        self.assertEqual(renderer_cls_two, renderer.get_section_renderer(section, extra_page, 'footer'))
        self.assertEqual(renderer_cls_three, renderer.get_section_renderer(section, main_page, 'sidebar'))
        self.assertEqual(renderer_cls_four, renderer.get_section_renderer(section, extra_page, 'sidebar'))

    def test_assets_registry(self):
        self.assertIn(TextSection, ASSETS_REGISTRY)
        self.assertIn(ExtraPage, ASSETS_REGISTRY)
        self.assertTrue(issubclass(ASSETS_REGISTRY[TextSection], TextSectionAssets))
        self.assertTrue(issubclass(ASSETS_REGISTRY[ExtraPage], ExtraPageAssets))

    def test_page_renderer(self):
        page = ExtraPage.objects.all()[0]
        renderer = get_page_renderer(page)(page)
        template_name = renderer.get_template_name()
        context = renderer.get_context()
        html = renderer.render()
        self.assertEqual(template_name, 'pages/extra_page.html')
        self.assertIn('special_info', context)
        self.assertIn(context['special_info'], html)
        self.assertIn(ExtraPageAssets.css, context['media']._css_lists)
        self.assertIn(TextSectionAssets.css, context['media']._css_lists)
        self.assertIn(ExtraPageAssets.js, context['media']._js_lists)
        self.assertIn(TextSectionAssets.js, context['media']._js_lists)
        for region, title in page.get_regions():
            self.assertIn(title, html)
            self.assertIn(region, context)
            self.assertIn('sections', context[region])
            self.assertIn(context[region], context['regions'])


class PageTests(TestDataMixin, TestCase):

    def test_resolve_page_obj(self):
        for page in Page.objects.all():
            child = page.resolve_obj()
            self.assertTrue(isinstance(child, (MainPage, ExtraPage)))


class UpdateIndexesTests(TestDataMixin, TestCase):

    def test_update_indexes_on_deleting(self):
        page = ExtraPage.objects.first()
        page_sections = PageSection.objects.filter(page=page, region='extra')

        # Get original indexes.
        old_indxs = dict(page_sections.values_list('id', 'index'))

        # Delete first item and reload indexes.
        page_sections.first().delete()
        page_sections = page_sections.all()
        new_indxs = dict(page_sections.values_list('id', 'index'))

        # Check that they were decreased by one.
        self.assertEqual(len(old_indxs) - 1, len(new_indxs))
        for id, index in new_indxs.items():
            self.assertEqual(index, old_indxs[id] - 1)

    def test_set_index_on_adding(self):
        page = MainPage.objects.first()
        section = Section.objects.first()
        page_sections = PageSection.objects.filter(page=page, region='main')
        last_index = page_sections.last().index
        new_page_section = PageSection.objects.create(
            page=page,
            region='main',
            section=section)
        self.assertEqual(new_page_section.index, last_index + 1)


class AdminBackendTests(TestDataMixin, TestCase):

    def setUp(self):
        self.client.force_login(User.objects.first())
        self.main_page_type = ContentType.objects.get(model='mainpage')
        self.extra_page_type = ContentType.objects.get(model='extrapage')

    def test_main_page_changeform_regions(self):
        page = Page.objects.filter(page_type=self.main_page_type).first()
        change_page_url = reverse('admin:simple_page_page_change', args=(page.id,))
        add_page_url = reverse('admin:simple_page_page_add')
        add_page_url = f'{add_page_url}?page_type={self.main_page_type.id}'

        for url in [change_page_url, add_page_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            for _, title in MainPage.get_regions():
                regex = r'<h2[^>]*>\s*{}\s*</h2>'.format(title)
                self.assertRegex(resp.content.decode('utf8'), regex)

    def test_extra_page_changeform_regions(self):
        page = Page.objects.filter(page_type=self.extra_page_type).first()
        change_page_url = reverse('admin:simple_page_page_change', args=(page.id,))
        change_extra_page_url = reverse('admin:test_project_extrapage_change', args=(page.id,))
        add_extra_page_url = reverse('admin:test_project_extrapage_add')

        for url in [change_page_url, change_extra_page_url, add_extra_page_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            for _, title in ExtraPage.get_regions():
                regex = r'<h2[^>]*>\s*{}\s*</h2>'.format(title)
                self.assertRegex(resp.content.decode('utf8'), regex)

    def test_choose_page_type_mixin(self):
        main_page_href = f'?page_type={self.main_page_type.id}'
        extra_page_url = reverse('admin:test_project_extrapage_add')
        url = reverse('admin:simple_page_page_add')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        for page_model in [MainPage, ExtraPage]:
            regex = r'<a[^>]+>\s*Add {}\s*</a>'.format(page_model._meta.verbose_name)
            self.assertRegex(resp.content.decode('utf8'), regex)
            self.assertIn(main_page_href, resp.content.decode('utf8'))
            self.assertIn(extra_page_url, resp.content.decode('utf8'))

    def test_set_page_type_mixin(self):
        add_page_url = reverse('admin:test_project_extrapage_add')
        resp = self.client.get(add_page_url)
        self.assertEqual(resp.status_code, 200)
        input = f'<input type="hidden" name="page_type" value="{self.extra_page_type.id}" id="id_page_type">'
        self.assertInHTML(input, resp.content.decode('utf8'))


class PageViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self.client.force_login(User.objects.first())

    def test_page_view(self):
        page = Page.objects.get(slug='home')
        url = reverse('page', kwargs=dict(slug=page.slug))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertInHTML(f'<h1>{page.title}</h1>', resp.content.decode('utf8'))

    def test_page_view_with_invalid_slug(self):
        url = reverse('page', kwargs={'slug': 'invalid_slug'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
