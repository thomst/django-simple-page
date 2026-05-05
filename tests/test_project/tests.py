import copy

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from simple_page.models import Page, PageSection, Section
from simple_page import renderer
from simple_page import assets

from .models import TextSection, MainPage, ExtraPage


class FixTestDataMixin:
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


class SetupRegistryMixin:

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reset_registries()
        cls.register_page_renderer()
        cls.register_section_renderer()
        cls.register_page_assets()
        cls.register_section_assets()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.restore_registries()

    @classmethod
    def reset_registries(cls):
        cls.renderer_registry = copy.deepcopy(renderer.REGISTRY)
        cls.assets_registry = copy.deepcopy(assets.REGISTRY)
        [renderer.REGISTRY.pop(k) for k in renderer.REGISTRY.copy()]
        [assets.REGISTRY.pop(k) for k in assets.REGISTRY.copy()]

    @classmethod
    def restore_registries(cls):
        [renderer.REGISTRY.pop(k) for k in renderer.REGISTRY.copy()]
        [assets.REGISTRY.pop(k) for k in assets.REGISTRY.copy()]
        renderer.REGISTRY.update(cls.renderer_registry)
        assets.REGISTRY.update(cls.assets_registry)

    @classmethod
    def register_page_renderer(cls):
        class BaseRenderer(renderer.PageRenderer):
            def get_context(self):
                context = super().get_context()
                context['extra'] = 'extra-data'
                return context
        cls.page_renderer = type('MainPageRenderer', (BaseRenderer,), dict())
        renderer.register(cls.page_renderer, MainPage)

    @classmethod
    def register_section_renderer(cls):
        cls.section_renderer = dict()
        for i in range(1, 5):
            class BaseRenderer(renderer.SectionRenderer):
                template_name = cls.template.name
                extra_data = f'extra-data-{i}'
                def get_context(self):
                    context = super().get_context()
                    context['extra'] = self.extra_data
                    return context
            cls.section_renderer[i] = (type(f'TextSection{i}Renderer', (BaseRenderer,), dict()))
        renderer.register(cls.section_renderer[1], TextSection, context=(MainPage, 'main'))
        renderer.register(cls.section_renderer[2], TextSection, context='footer')
        renderer.register(cls.section_renderer[3], TextSection, context=MainPage)
        renderer.register(cls.section_renderer[4], TextSection)

    @classmethod
    def register_page_assets(cls):
        cls.page_assets = type('TestPageAssets', (assets.Assets,), dict())
        assets.register(cls.page_assets, MainPage)

    @classmethod
    def register_section_assets(cls):
        cls.section_assets = dict()
        for i in range(1, 5):
            attrs = dict(js=[f'text_section_{i}.js'], css=dict(all=[f'text_section_{i}.css']))
            cls.section_assets[i] = (type(f'TextSection{i}Assets', (assets.Assets,), attrs))
        assets.register(cls.section_assets[1], TextSection, context=(MainPage, 'main'))
        assets.register(cls.section_assets[2], TextSection, context='footer')
        assets.register(cls.section_assets[3], TextSection, context=MainPage)
        assets.register(cls.section_assets[4], TextSection)



class RendererRegistryTests(SetupRegistryMixin, FixTestDataMixin, TestCase):

    def test_page_renderer_registry(self):
        page = MainPage.objects.all()[0]
        self.assertEqual(self.page_renderer, renderer.get_page_renderer(page))

    def test_section_renderer_register(self):
        section = TextSection.objects.all()[0]
        main_page = MainPage.objects.all()[0]
        extra_page = ExtraPage.objects.all()[0]

        self.assertEqual(self.section_renderer[1], renderer.get_section_renderer(section, main_page, 'main'))
        self.assertEqual(self.section_renderer[2], renderer.get_section_renderer(section, main_page, 'footer'))
        self.assertEqual(self.section_renderer[2], renderer.get_section_renderer(section, extra_page, 'footer'))
        self.assertEqual(self.section_renderer[3], renderer.get_section_renderer(section, main_page, 'sidebar'))
        self.assertEqual(self.section_renderer[4], renderer.get_section_renderer(section, extra_page, 'sidebar'))


class AssetsRegistryTests(SetupRegistryMixin, FixTestDataMixin, TestCase):

    def test_page_assets_registry(self):
        page = MainPage.objects.all()[0]
        self.assertEqual(self.page_assets, assets.get_page_assets(page))

    def test_section_assets_register(self):
        section = TextSection.objects.all()[0]
        main_page = MainPage.objects.all()[0]
        extra_page = ExtraPage.objects.all()[0]

        # Check the get_section_assets function.
        self.assertEqual(self.section_assets[1], assets.get_section_assets(section, main_page, 'main'))
        self.assertEqual(self.section_assets[2], assets.get_section_assets(section, main_page, 'footer'))
        self.assertEqual(self.section_assets[2], assets.get_section_assets(section, extra_page, 'footer'))
        self.assertEqual(self.section_assets[3], assets.get_section_assets(section, main_page, 'sidebar'))
        self.assertEqual(self.section_assets[4], assets.get_section_assets(section, extra_page, 'sidebar'))


class PageRendererTests(ResetRegistryMixin, FixTestDataMixin, TestCase):

    def setUp(self):
        pass

    def test_page_renderer(self):
        page = ExtraPage.objects.all()[0]
        page_renderer = renderer.get_page_renderer(page)(page)
        template_name = page_renderer.get_template_name()
        context = page_renderer.get_context()
        html = page_renderer.render()
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


class PageTests(FixTestDataMixin, TestCase):

    def test_resolve_page_obj(self):
        for page in Page.objects.all():
            child = page.resolve_obj()
            self.assertTrue(isinstance(child, (MainPage, ExtraPage)))


class UpdateIndexesTests(FixTestDataMixin, TestCase):

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


class AdminBackendTests(FixTestDataMixin, TestCase):

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


class PageViewTests(FixTestDataMixin, TestCase):

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
