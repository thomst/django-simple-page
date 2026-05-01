from mptt.models import MPTTModel, TreeForeignKey
from model_utils.managers import InheritanceManager

from django.db import models
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType


class Section(models.Model):
    """
    This model is the base model for what ever content you want to see on your
    website. It does not has any fields on its own but provides a many-to-many
    relationship to the `Page` model.
    """
    objects = InheritanceManager()

    def __str__(self):
        if type(self) is Section:
            child_self = self._meta.model.objects.get_subclass(id=self.id)
            return f"{child_self._meta.verbose_name}: {child_self}"
        else:
            return super().__str__()


class Page(MPTTModel):
    """
    This is the base model for all pages. The only thing a subclass has to do is
    to setup the regions it wants to use. Since the database layout of the base
    class is fully functional, it is totally sufficient to define your page
    model as a proxy. Still you are free to use a concrete child model with all
    the additional fields and logic you whish for.

    The sections of a page are available as a region specific queryset using the
    region's name as an object attribute.

    The base model takes care of the following things:
    - As a `mptt` model it allows to arrange pages in treelike structures.
    - It has a region specific many-to-many relationship to the `Section` model.
    - It has a `slug` field which can be used in your url path.
    - It has a `ContentType` relation that points to the Page's child class.
    - It provides some logic to handle the regions a subclass sets.
    """

    # FIXME: We should use REGIONS = None and raise a NotImplementedError. But
    # tests are failing, since for any reason the get_regions method is called
    # on a Page objects occacionally.
    REGIONS = []
    """
    REGIONS must be set by a subclass as a list of tuples holding the region's
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


class UpdateIndexesManager(models.Manager):
    """
    Provide methods to set the index of an newly saved object and to fix
    indexes of a set of items from which one was deleted.
    """
    def set_index(self, obj):
        """
        If an object is about to be added we give him the next higher
        index. Call this method from a pre-save signal handler.
        """
        items = self.filter(page=obj.page, region=obj.region)
        max_index = items.aggregate(models.Max('index'))['index__max'] or 0
        obj.index = max_index + 1

    def update_indexes(self, obj):
        """
        If an object was deleted fix the indexes of following objects. Call this
        method from a post-delete signal handler.
        """
        items = self.filter(page=obj.page, region=obj.region)
        for item in items.filter(index__gt=obj.index):
            item.index -= 1
            item.save()


class PageSection(models.Model):
    """
    Assign sections to regions on pages using PageSection as an intermediate
    model for the many-to-many relation between the Page and the Section model.
    We also provide an index field to make page-sections orderable.
    """
    objects = UpdateIndexesManager()

    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    region = models.CharField('Region', max_length=255)
    index = models.SmallIntegerField(blank=True)

    class Meta:
        ordering = ["page__id", "index"]

    def __str__(self):
        return f"{self.section}"
