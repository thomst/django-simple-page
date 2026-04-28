from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from simple_page.models import Page, PageSection, Section
from simple_page.renderer import REGISTRY as RENDERER_REGISTRY
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


class SimplePageTests(TestDataMixin, TestCase):
    def test_renderer_registry(self):
        self.assertIn(TextSection, RENDERER_REGISTRY)
        self.assertIn(ExtraPage, RENDERER_REGISTRY)
        self.assertTrue(issubclass(RENDERER_REGISTRY[TextSection], TextSectionRenderer))
        self.assertTrue(issubclass(RENDERER_REGISTRY[ExtraPage], ExtraPageRenderer))

    def test_assets_registry(self):
        self.assertIn(TextSection, ASSETS_REGISTRY)
        self.assertIn(ExtraPage, ASSETS_REGISTRY)
        self.assertTrue(issubclass(ASSETS_REGISTRY[TextSection], TextSectionAssets))
        self.assertTrue(issubclass(ASSETS_REGISTRY[ExtraPage], ExtraPageAssets))

    def test_page_renderer(self):
        page = ExtraPage.objects.all()[0]
        renderer = RENDERER_REGISTRY[type(page)](page)
        template_name = renderer.get_template_name()
        context = renderer.get_context(None)
        html = renderer.render(None)
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
        page_url = reverse('admin:simple_page_page_change', args=(page.id,))

        resp = self.client.get(page_url)
        self.assertEqual(resp.status_code, 200)
        for _, title in MainPage.get_regions():
            regex = r'<h2[^>]+>\s*{}\s*</h2>'.format(title)
            self.assertRegex(resp.content.decode('utf8'), regex)

    def test_extra_page_changeform_regions(self):
        page = Page.objects.filter(page_type=self.extra_page_type).first()
        page_url = reverse('admin:simple_page_page_change', args=(page.id,))
        extra_page_url = reverse('admin:test_project_extrapage_change', args=(page.id,))

        for url in [page_url, extra_page_url]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            for _, title in ExtraPage.get_regions():
                regex = r'<h2[^>]+>\s*{}\s*</h2>'.format(title)
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
