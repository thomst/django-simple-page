"""
Pages and sections are the basic building blocks of your website. Pages define
regions in which sections can be placed. And sections can be any kind of content
you want to see on your website.

Pages and sections are defined by subclassing the :class:`~.models.Page` and
:class:`~.models.Section` model::

    from simple_page.models import Page, Section

    class FancyPage(Page):
        REGIONS = [
            ('main', 'Main Region'),
            ('sidebar', 'Sidebar'),
            ('footer', 'Footer'),
        ]

        class Meta:
            proxy = True


    class FancySection(Section):
        title = models.CharField(max_length=255, blank=True)
        text = models.TextField(blank=True)


With those two models you are able to build a simple website.
"""

from mptt.models import MPTTModel, TreeForeignKey
from model_utils.managers import InheritanceManager

from django.db import models
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType

from reorder_items_widget import ReorderItemsField


class Section(models.Model):
    """
    Base model for what ever content you want to see on your website. It does
    not has any fields by its own but can be equipped by sublcasses.

    Sections are related to pages via a many-to-many relationship that holds the
    region in which a section should be rendered and an index field to make the
    sections orderable whithin that region.
    """

    objects = InheritanceManager()
    """
    We use the `InheritanceManager`_ to provide a simple api to access child
    class objects.

    .. _InheritanceManager: https://django-model-utils.readthedocs.io/en/latest/managers.html#inheritancemanager
"""

    def __str__(self):
        if type(self) is Section:
            child_self = self._meta.model.objects.get_subclass(id=self.id)
            return f"{child_self._meta.verbose_name}: {child_self}"
        else:
            # FIXME: This leads to a recursive call if child_self is a Section
            # as well. This happens when for any reason a section object has no
            # child class.
            return super().__str__()


class Page(MPTTModel):
    """
    Base model for all pages.

    The only thing a subclass has to do is to setup its :attr:`regions
    <.Page.REGIONS>`. Since the database layout is fully functional, you may
    define your own page model as a proxy if you do not want to provide
    additional fields.

    Sections associated with a page are accessible by their region. Use the
    region's name to get a queryset of sections belonging to that region.

    The page model is tree structured by `django-mptt`_.

    .. _django-mptt: https://django-mptt.readthedocs.io/en/latest/
    """

    # FIXME: We should use REGIONS = None and raise a NotImplementedError. But
    # tests are failing, since for any reason the get_regions method is called
    # on a Page objects occacionally.
    REGIONS = []
    """
    REGIONS must be set by subclasses as a list of tuples holding the region's
    name and its title. Something like::

        REGIONS = [
            ('main', 'Main Region'),
            ('sidebar', 'Sidebar'),
            ('footer', 'Footer'),
        ]
    """

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


class PageSection(models.Model):
    """
    PageSection is the intermediate model for the many-to-many relationship
    between pages and sections. It holds the region in which a section should be
    rendered and an index field to make sections orderable whithin that region.
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    region = models.CharField('Region', max_length=255)
    index = ReorderItemsField('Index', grouped_by=['page', 'region'])

    class Meta:
        ordering = ["page", "region", "index"]

    def __str__(self):
        return f"{self.section}"
