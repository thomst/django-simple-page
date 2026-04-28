from django.test import TestCase
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from simple_page.models import Page, PageSection, Section
from simple_page.renderer import REGISTRY as RENDERER_REGISTRY
from simple_page.assets import REGISTRY as ASSETS_REGISTRY

from .models import TextSection, TextWithTitleSection, MainPage, ExtraPage
from .renderer import TextSectionRenderer, ExtraPageRenderer
from .assets import TextSectionAssets, ExtraPageAssets


class SimplePageTests(TestCase):
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
            self.assertTrue(isinstance(child, MainPage) or isinstance(child, ExtraPage))
