from django.db import models

from simple_page.models import Section
from simple_page.models import Page


class TextSection(Section):
    """A content model that extends the base Section model."""

    title = models.CharField(max_length=255)
    text = models.TextField(blank=True)

    class Meta:
        verbose_name = "Text Section"
        verbose_name_plural = "Text Sections"

    def __str__(self):
        return self.title


class ImageSection(Section):
    """An image model that extends the base Section model."""

    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="section_images/")

    class Meta:
        verbose_name = "Image Section"
        verbose_name_plural = "Image Sections"

    def __str__(self):
        return self.title


class MainPage(Page):
    def method(self):
        print('hello')
