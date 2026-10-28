from django.db import models
from django.urls import reverse

from simple_page.models import Section
from simple_page.models import Page


class TextSection(Section):

    title = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)

    def __str__(self):
        return self.title or f'{self.text[:8]} ...'


class FooterSection(Section):

    title = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)

    def __str__(self):
        return self.title or f'{self.text[:8]} ...'


class GetUrlMixin:
    def get_absolute_url(self):
        return reverse('page', kwargs={'slug': self.slug})


class MainPage(GetUrlMixin, Page):
    REGIONS = [
        ('sidebar', 'Sidebar'),  # Not really used for section.
        ('main', 'Main Region'),
        ('footer', 'Footer'),
    ]
    REGION_SECTIONS = {
        'main': [TextSection],
        'footer': [FooterSection],
    }

    class Meta:
        proxy = True


class PageWithHeader(GetUrlMixin, Page):
    REGIONS = [
        ('header', 'Header'),  # Not really used for section.
        ('sidebar', 'Sidebar'),  # Not really used for section.
        ('main', 'Main Region'),
        ('footer', 'Footer'),
    ]
    REGION_SECTIONS = {
        'header': [TextSection, FooterSection],  # Just for testing.
        'main': [TextSection],
        'footer': [FooterSection],
    }

    header_info = models.CharField(max_length=255, blank=True)


class PageWithoutGetAbsoluteUrl(Page):
    REGIONS = [
        ('sidebar', 'Sidebar'),  # Not really used for section.
        ('main', 'Main Region'),
        ('footer', 'Footer'),
    ]

    class Meta:
        proxy = True
