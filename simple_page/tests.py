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


class SectionTests(TemplateDirMixin, TestCase):
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


class PageTests(TemplateDirMixin, TestCase):
    def test_get_absolute_url(self):
        page = Page.objects.create(title='Home', slug='home')
        self.assertEqual(page.get_absolute_url(), reverse('page', kwargs={'slug': 'home'}))


class OrderedRelationTests(TestCase):
    def setUp(self):
        self.page_sections = list()
        page = Page.objects.create(title='Home', slug='home')
        self.page = page
        for i in range(3):
            section = Section.objects.create()
            self.page_sections.append(
                PageSection.objects.create(page=page, section=section)
            )
        # self.section1 = Section.objects.create()
        # self.section2 = Section.objects.create()
        # self.section3 = Section.objects.create()

    def test_add_item_assigns_next_index(self):
        # Creating page-sections calls add_item method via pre-save signal. So
        # they indexes should be set properly.
        self.assertEqual([ps.index for ps in self.page_sections], [1, 2, 3])

    def test_delete_item_decrements_following_indexes(self):
        section_page = self.page_sections.pop(0)
        section_page.delete() # This calls delete_item method via post-delete signal handler.
        [ps.refresh_from_db() for ps in self.page_sections]
        self.assertEqual([ps.index for ps in self.page_sections], [1, 2])

    def test_move_item_up_switch_indexes_with_preceding_item(self):
        self.page_sections[1].move_item_up()
        [ps.refresh_from_db() for ps in self.page_sections]
        self.assertEqual([ps.index for ps in self.page_sections], [2, 1, 3])

    def test_move_item_down_switch_indexes_with_following_item(self):
        self.page_sections[1].move_item_down()
        [ps.refresh_from_db() for ps in self.page_sections]
        self.assertEqual([ps.index for ps in self.page_sections], [1, 3, 2])
