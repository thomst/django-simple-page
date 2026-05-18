from django.db import models

from simple_page.models import Section
from simple_page.models import Page
from simple_page import renderer

from .renderer import ExtraPageRenderer


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
        ('extra', 'Extra Region'),
        *MainPage.REGIONS
    ]

    special_info = models.CharField(max_length=255, blank=True)


class TextSection(Section):

    title = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)

    def __str__(self):
        return self.title or f'{self.text[:8]} ...'
