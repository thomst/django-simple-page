import os
import copy
import re
import tempfile
from pathlib import Path

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.template import Template, Context

from simple_page.models import Page, PageSection, Section
from simple_page import renderers
from simple_page import __version__

from .models import TextSection, MainPage, PageWithHeader


class TestDataMixin:
    fixtures = ['testdata.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Fix the page_type references. The ids in the page fixtures might not
        # fit to the real content type ids.
        header_pages = PageWithHeader.objects.all()
        header_page_type = ContentType.objects.get(model='pagewithheader')
        main_pages = Page.objects.exclude(id__in=[p.id for p in header_pages])
        main_page_type = ContentType.objects.get(model='mainpage')
        for page in header_pages:
            page.page_type = header_page_type
            page.save()
        for page in main_pages:
            page.page_type = main_page_type
            page.save()


class AddSectionsMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        page = MainPage.objects.first()
        for region, _ in MainPage.get_regions():
            cls.add_section(page, region)

    @staticmethod
    def add_section(page, region, text='foobar'):
        section = TextSection.objects.create(text=text)
        PageSection.objects.create(page=page, section=section, region=region)


class SetupRendererMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reset_registry()
        cls.setup_templates()
        cls.register_page_renderer()
        cls.register_section_renderer()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.restore_registry()
        cls.remove_templates()

    @classmethod
    def reset_registry(cls):
        cls.renderer_registry = copy.deepcopy(renderers.REGISTRY)
        [renderers.REGISTRY.pop(k) for k in renderers.REGISTRY.copy()]

    @classmethod
    def restore_registry(cls):
        [renderers.REGISTRY.pop(k) for k in renderers.REGISTRY.copy()]
        renderers.REGISTRY.update(cls.renderer_registry)

    @classmethod
    def setup_templates(cls):
        test_project_dir = Path(__file__).resolve().parent

        # Page template.
        html = b'{% extends "pages/main_page.html" %}{% block content %}{{ block.super }}<p>{{ extra }}</p>{% endblock %}'
        template_dir = test_project_dir / 'templates' / 'pages'
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = tempfile.NamedTemporaryFile(dir=str(template_dir), delete=False)
        with template_file as cls.page_template:
            cls.page_template.write(html)

        # Section template.
        html = b'<h3>{{ extra }}</h3><p>{{ section.text }}</p>'
        template_dir = test_project_dir / 'templates' / 'sections'
        template_dir.mkdir(parents=True, exist_ok=True)
        template_file = tempfile.NamedTemporaryFile(dir=str(template_dir), delete=False)
        with template_file as cls.section_template:
            cls.section_template.write(html)

    @classmethod
    def remove_templates(cls):
        os.remove(cls.page_template.name)
        os.remove(cls.section_template.name)

    @classmethod
    def register_page_renderer(cls):
        class BaseRenderer(renderers.PageRenderer):
            extra_data = 'extra-page-data'

            class Media:
                css = dict(all=['pages/main_page.css'])
                js = ['pages/main_page.js']

            def get_template_name(self):
                return cls.page_template.name

            def get_context_data(self, **context):
                context = super().get_context_data(**context)
                context['extra'] = self.extra_data
                return context

        cls.page_renderer = type('MainPageRenderer', (BaseRenderer,), dict())
        renderers.register(MainPage, cls.page_renderer)

    @classmethod
    def register_section_renderer(cls):
        class BaseRenderer(renderers.SectionRenderer):
            extra_data = 'extra-section-data'

            class Media:
                css = dict(all=[f'text_section.css'])
                js = [f'text_section.js']

            def get_template_name(self):
                return cls.section_template.name

            def get_region_data(self):
                return f'{{ self.page }}.{{ self.region }}.{{ self.section }}'

            def get_context_data(self, **context):
                context = super().get_context_data(**context)
                context['extra'] = self.extra_data
                context['region_data'] = self.get_region_data()
                return context

        cls.section_renderer = (type('TextSectionRenderer', (BaseRenderer,), dict()))
        renderers.register(TextSection, cls.section_renderer)


class RendererRegistryTests(SetupRendererMixin, TestDataMixin, TestCase):

    def test_page_renderer_registry(self):
        page = MainPage.objects.first()
        self.assertEqual(self.page_renderer, renderers.get_renderer(page))

    def test_section_renderer_register(self):
        section = TextSection.objects.first()
        self.assertEqual(self.section_renderer, renderers.get_renderer(section))


class PageRendererTests(AddSectionsMixin, SetupRendererMixin, TestDataMixin, TestCase):

    def setUp(self):
        self.page = MainPage.objects.first()
        self.section = TextSection.objects.first()
        self.page_renderer_class = renderers.get_renderer(self.page)
        self.page_renderer = self.page_renderer_class(self.page)
        self.section_renderer_class = renderers.get_renderer(self.section)
        self.section_renderer = self.section_renderer_class(self.section, self.page, 'main')
        return super().setUp()

    def test_template_name(self):
        template_name = renderers.PageRenderer(self.page).get_template_name()
        self.assertEqual(template_name, 'pages/main_page.html')

    def test_context_keys(self):
        context = self.page_renderer.get_context_data()
        self.assertIn('page', context)
        self.assertIn('extra', context)
        self.assertIn('media', context)
        self.assertIn('regions', context)
        self.assertIn('sections', context)
        for region in self.page.get_regions():
            self.assertIn(region[0], context)
            self.assertIn(region[0], context['regions'])
            self.assertIn('sections', context[region[0]])

    def test_media_context(self):
        media = str(self.page_renderer.get_context_data()['media'])

        # Check Media class definitions and media property of section renderer.
        for path in self.section_renderer_class.Media.css['all']:
            self.assertIn(path, media)
        for path in self.section_renderer_class.Media.js:
            self.assertIn(path, media)
        for path in str(self.section_renderer.media).splitlines():
            self.assertIn(path, media)

        # Check Media class definitions and media property of page renderer.
        for path in self.page_renderer_class.Media.css['all']:
            self.assertIn(path, media)
        for path in self.page_renderer_class.Media.js:
            self.assertIn(path, media)
        for path in str(self.page_renderer.media).splitlines():
            self.assertIn(path, media)

    def test_html(self):
        html = self.page_renderer.render()
        context = self.page_renderer.get_context_data()

        # Check secion-renderers' extra_data.
        self.assertIn(self.page_renderer.extra_data, html)
        self.assertIn(self.section_renderer.extra_data, html)

        # Check regions.
        for region, title in self.page.get_regions():

            # Check regions title rendering.
            self.assertIn(title, html)

            # Check region specific data
            sections = [s for s in context[region]['sections'] if s.section is self.section]
            for section in sections:
                region_data = section.get_region_data()
                print(region_data)
                self.assertIn(region_data, html)


class PageTests(AddSectionsMixin, TestDataMixin, TestCase):

    def test_resolve_page_obj(self):
        for page in Page.objects.all():
            child = page.resolve_obj()
            self.assertTrue(isinstance(child, (MainPage, PageWithHeader)))

    def test_get_regions(self):
        page = MainPage.objects.first()
        for region, _ in page.get_regions():
            self.assertTrue(hasattr(page, region))
            for section in getattr(page, region).all():
                # The section queryset uses select_subclasses.
                self.assertIsInstance(section, TextSection)

        # Raise AttributeError for non existing region.
        with self.assertRaises(AttributeError):
            page.non_existing_region


class UpdateIndexesTests(TestDataMixin, TestCase):

    def test_update_indexes_on_deleting(self):
        page = MainPage.objects.first()
        page_sections = PageSection.objects.filter(page=page, region='main')

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
        self.header_page_type = ContentType.objects.get(model='pagewithheader')

    def test_page_list_view(self):
        url = reverse('admin:simple_page_page_changelist')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        for page in Page.objects.all():
            regex = r'<a[^>]+>\s*{}\s*</a>'.format(page.title)
            self.assertRegex(resp.content.decode('utf8'), regex)

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

    def test_header_page_changeform_regions(self):
        page = Page.objects.filter(page_type=self.header_page_type).first()
        change_page_url = reverse('admin:simple_page_page_change', args=(page.id,))
        change_header_page_url = reverse('admin:test_project_pagewithheader_change', args=(page.id,))
        add_header_page_url = reverse('admin:test_project_pagewithheader_add')

        for url in [change_page_url, change_header_page_url, add_header_page_url]:
            resp = self.client.get(url, follow=True)
            self.assertEqual(resp.status_code, 200)
            for _, title in PageWithHeader.get_regions():
                regex = r'<h2[^>]*>\s*{}\s*</h2>'.format(title)
                self.assertRegex(resp.content.decode('utf8'), regex)

    def test_choose_page_type_mixin(self):
        main_page_href = f'?page_type={self.main_page_type.id}'
        header_page_url = reverse('admin:test_project_pagewithheader_add')
        url = reverse('admin:simple_page_page_add')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        for page_model in [MainPage, PageWithHeader]:
            regex = r'<a[^>]+>\s*Add {}\s*</a>'.format(page_model._meta.verbose_name)
            self.assertRegex(resp.content.decode('utf8'), regex)
            self.assertIn(main_page_href, resp.content.decode('utf8'))
            self.assertIn(header_page_url, resp.content.decode('utf8'))

    def test_get_page_type_mixin_with_invalid_id(self):
        url = f"{reverse('admin:simple_page_page_add')}?page_type=9999"
        self.assertRaises(ValueError, self.client.get, url)

    def test_set_page_type_mixin(self):
        add_page_url = reverse('admin:test_project_pagewithheader_add')
        resp = self.client.get(add_page_url)
        self.assertEqual(resp.status_code, 200)
        input = f'<input type="hidden" name="page_type" value="{self.header_page_type.id}" id="id_page_type">'
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


class MenuTemplateTagTests(TestDataMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.href_regex = r'<a[^>]+href="{}"[^>]*>\s*{}\s*</a>'
        super().setUpClass()

    def test_menu_template_tag_with_root(self):
        template = Template('{% load simple_page %}{% menu page include_root=True %}')
        page = Page.objects.first()
        context = Context({'page': page})
        rendered = template.render(context)
        for page in Page.objects.all():
            regex = self.href_regex.format(re.escape(page.get_absolute_url()), re.escape(page.title))
            self.assertRegex(rendered, regex)

    def test_menu_template_tag_without_root(self):
        template = Template('{% load simple_page %}{% menu page include_root=False %}')
        page = Page.objects.first()
        context = Context({'page': page})
        rendered = template.render(context)
        for page in Page.objects.all():
            regex = self.href_regex.format(re.escape(page.get_absolute_url()), re.escape(page.title))
            if page.is_root_node():
                self.assertNotRegex(rendered, regex)
            else:
                self.assertRegex(rendered, regex)

    def test_menu_template_tag_with_max_level(self):
        for max_level in range(1, 4):
            template = Template(f'{{% load simple_page %}}{{% menu page include_root=True max_level={max_level} %}}')
            page = Page.objects.first()
            context = Context({'page': page})
            rendered = template.render(context)
            for page in Page.objects.all():
                regex = self.href_regex.format(re.escape(page.get_absolute_url()), re.escape(page.title))
                if page.is_root_node() or page.get_ancestors().count() <= max_level:
                    self.assertRegex(rendered, regex)
                else:
                    self.assertNotRegex(rendered, regex)

    def test_is_active_template_filter(self):
        template = Template('{% load simple_page %}{% menu page %}')
        for page in Page.objects.all():
            context = Context({'page': page})
            rendered = template.render(context)
            for node in Page.objects.all():
                if node.is_root_node():
                    continue
                href_regex = self.href_regex.format(re.escape(node.get_absolute_url()), re.escape(node.title))
                regex = r'<li class="active">\s*{}'.format(href_regex)
                if node in context['page'].get_ancestors(include_self=True):
                    self.assertRegex(rendered, regex)
                else:
                    self.assertNotRegex(rendered, regex)


class PageChangeViewTests(TestDataMixin, TestCase):

    def setUp(self):
        self.client.force_login(User.objects.first())

    def test_proxy_page_change_view(self):
        obj = MainPage.objects.first()
        url = reverse('admin:simple_page_page_change', args=(obj.id,))
        resp = self.client.get(url, follow=True)
        self.assertFalse(resp.redirect_chain)
        self.assertEqual(resp.status_code, 200)

    def test_redirect_concrete_page_change_view(self):
        obj = PageWithHeader.objects.first()
        url = reverse('admin:simple_page_page_change', args=(obj.page_ptr.id,))
        redirect_url = reverse('admin:test_project_pagewithheader_change', args=(obj.id,))
        resp = self.client.get(url, follow=True)
        self.assertTrue(resp.redirect_chain)
        self.assertEqual(resp.redirect_chain[0][0], redirect_url)
        self.assertEqual(resp.redirect_chain[0][1], 301)
        self.assertEqual(resp.status_code, 200)
