from django.db import models

from simple_page.models import Section
from simple_page.models import Page
from simple_page import renderer

from .renderer import PageWithHeaderRenderer


class MainPage(Page):
    REGIONS = [
        ('main', 'Main Region'),
        ('sidebar', 'Sidebar'),
        ('footer', 'Footer'),
    ]

    class Meta:
        proxy = True


@renderer.register(PageWithHeaderRenderer)
class PageWithHeader(Page):
    REGIONS = [
        ('header', 'Header'),
        *MainPage.REGIONS
    ]

    header_info = models.CharField(max_length=255, blank=True)


class TextSection(Section):

    title = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)

    def __str__(self):
        return self.title or f'{self.text[:8]} ...'
