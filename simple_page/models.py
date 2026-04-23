import re

from mptt.models import MPTTModel, TreeForeignKey
from model_utils.managers import InheritanceManager

from django.db import models
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType


class Section(models.Model):
    """
    A base model for content sections that can be added to pages.

    This model is ment as a base model for all section types, which can be any
    content type you want to see on your website. It does not contain any fields
    itself, but provides a common interface for rendering the section as HTML
    which can be customized by child classes.
    """
    objects = InheritanceManager()

    def __str__(self):
        if type(self) is Section:
            child_self = self._meta.model.objects.get_subclass(id=self.id)
            return f"{child_self.__class__.__name__}: {child_self}"
        else:
            return super().__str__()


class Page(MPTTModel):
    """
    A model holding everything to render a simple web page:
    - a slug for the URL for the page
    - the base page to create navigation menus
    - regions and sections to render the content of the page
    - a routine to get the template to render the page
    """
    REGIONS = []

    @classmethod
    def get_regions(cls):
        """
        Return the regions for this page. This method can be customized by child
        classes to return different regions.
        """
        return cls.REGIONS

    def resolve_obj(self):
        """
        Return the instance of the child class.
        """
        model = self.page_type.model_class()
        return model.objects.get(id=self.id)

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    page_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    sections = models.ManyToManyField(
        Section,
        through="PageSection",
        related_name="pages",
        blank=True,
    )
    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )

    def get_absolute_url(self):
        return reverse("page", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title

    def __getattr__(self, name):
        """
        If the attribute name is a region return its sections, otherwise raise
        AttributeError.
        """
        if name in [region for region, _ in self.get_regions()]:
            sections = self.sections.filter(pagesection__region=name)
            return sections.select_subclasses().order_by("pagesection__index")
        else:
            msg = f"{self.__class__.__name__} object has no attribute '{name}'"
            raise AttributeError(msg)


class OrderedRelationMixin:
    """
    Mixin to update indexes on deleting and adding items.
    """
    def _get_item_set(self):
        if hasattr(self, 'page'):
            kwargs = {'page': self.page}
        else:
            kwargs = {'region': self.region}
        return type(self).objects.filter(**kwargs)

    def update_indexes_on_deleting(self):
        """
        Decrease index by one for all following items. Run this method after
        items was deleted.
        """
        items = self._get_item_set()
        for item in items.filter(index__gt=self.index):
            item.index -= 1
            item.save()

    def update_indexes_on_adding(self):
        """
        Set max index + 1 for item. Run this method before item was saved.
        """
        items = self._get_item_set()
        max_index = items.aggregate(models.Max('index'))['index__max'] or 0
        self.index = max_index + 1


class PageSection(OrderedRelationMixin, models.Model):
    """
    Ordered many-to-many relation between pages and sections.
    """

    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    region = models.CharField('Region', max_length=255)
    index = models.SmallIntegerField(blank=True)

    class Meta:
        ordering = ["page__id", "index"]

    def __str__(self):
        return f"{self.section}"
