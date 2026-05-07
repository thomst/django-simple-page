from django.db import models

from simple_page.models import Section
from simple_page.models import Page
from simple_page import renderer

from .renderer import TextSectionRenderer, ExtraPageRenderer, ExtraSectionRenderer


class MainPage(Page):
    REGIONS = [
        ('main', 'Main Region'),
        ('sidebar', 'Sidebar'),
        ('footer', 'Footer'),
    ]

    class Meta:
        proxy = True


@renderer.register(ExtraPageRenderer)
class ExtraPage(Page):
    REGIONS = [
        ('main', 'Main Region'),
        ('extra', 'Extra Region'),
        ('sidebar', 'Sidebar'),
        ('footer', 'Footer'),
    ]

    special_info = models.CharField(max_length=255, blank=True)


@renderer.register(TextSectionRenderer)
@renderer.register(ExtraSectionRenderer, context=(ExtraPage, 'extra'))
class TextSection(Section):

    text = models.TextField(blank=True)

    def __str__(self):
        return f'{self.text[:8]}...'


class TextWithTitleSection(Section):

    title = models.CharField(max_length=255)
    text = models.TextField(blank=True)

    def __str__(self):
        return self.title

