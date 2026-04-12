import os
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Page, PageSection, Section


class TemplateDirMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.templates_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(cls.templates_dir, 'sections'), exist_ok=True)
        os.makedirs(os.path.join(cls.templates_dir, 'pages'), exist_ok=True)
        with open(os.path.join(cls.templates_dir, 'sections', 'section.html'), 'w') as handle:
            handle.write('Section: {{ section }}')
        with open(os.path.join(cls.templates_dir, 'pages', 'page.html'), 'w') as handle:
            handle.write('Page: {{ page.slug }}')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.templates_dir)
        super().tearDownClass()

    def override_template_settings(self):
        return override_settings(
            TEMPLATES=[
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [self.templates_dir],
                    'APP_DIRS': True,
                    'OPTIONS': {
                        'context_processors': [
                            'django.template.context_processors.request',
                        ],
                    },
                }
            ]
        )


class MixinModelTests(TemplateDirMixin, TestCase):
    def test_get_child_instance_returns_none_for_base_section(self):
        section = Section.objects.create()
        self.assertIsNone(section.get_child_instance())

    def test_get_template_name_uses_snake_case(self):
        section = Section.objects.create()
        self.assertEqual(section.get_template_name(), 'sections/section.html')

    def test_render_uses_template_name(self):
        section = Section.objects.create()
        with self.override_template_settings():
            rendered = section.render()
        self.assertIn('Section:', rendered)
        self.assertIn('Section', rendered)

    def test_html_property_calls_render(self):
        section = Section.objects.create()
        with self.override_template_settings():
            self.assertEqual(section.html, section.render())


class PageModelTests(TemplateDirMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(os.path.join(cls.templates_dir, 'pages', 'home.html'), 'w') as handle:
            handle.write('Home page: {{ page.slug }}')

    def test_get_absolute_url(self):
        page = Page.objects.create(title='Home', slug='home')
        self.assertEqual(page.get_absolute_url(), reverse('page', kwargs={'slug': 'home'}))


class OrderedRelationMixinTests(TestCase):
    def setUp(self):
        self.page = Page.objects.create(title='Home', slug='home')
        self.section1 = Section.objects.create()
        self.section2 = Section.objects.create()
        self.section3 = Section.objects.create()

    def test_add_item_assigns_next_index(self):
        page_section = PageSection(page=self.page, section=self.section1)
        page_section.add_item()
        page_section.save()
        self.assertEqual(page_section.index, 1)

        second_section = PageSection(page=self.page, section=self.section2)
        second_section.add_item()
        second_section.save()
        self.assertEqual(second_section.index, 2)

    def test_delete_item_decrements_following_indexes(self):
        first = PageSection.objects.create(page=self.page, section=self.section1, index=1)
        second = PageSection.objects.create(page=self.page, section=self.section2, index=2)
        third = PageSection.objects.create(page=self.page, section=self.section3, index=3)
        first.delete() # This calls first.delete_item() via the signal handler.
        second.refresh_from_db()
        third.refresh_from_db()
        self.assertEqual(second.index, 1)
        self.assertEqual(third.index, 2)

    def test_move_item_up_switch_indexes_with_preceding_item(self):
        first = PageSection.objects.create(page=self.page, section=self.section1, index=1)
        second = PageSection.objects.create(page=self.page, section=self.section2, index=2)
        third = PageSection.objects.create(page=self.page, section=self.section3, index=3)
        second.move_item_up()
        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()
        self.assertEqual(first.index, 2)
        self.assertEqual(second.index, 1)
        self.assertEqual(third.index, 3)

    def test_move_item_down_switch_indexes_with_following_item(self):
        first = PageSection.objects.create(page=self.page, section=self.section1, index=1)
        second = PageSection.objects.create(page=self.page, section=self.section2, index=2)
        third = PageSection.objects.create(page=self.page, section=self.section3, index=3)
        second.move_item_down()
        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()
        self.assertEqual(first.index, 1)
        self.assertEqual(second.index, 3)
        self.assertEqual(third.index, 2)
