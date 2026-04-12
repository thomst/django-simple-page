import re

from mptt.models import MPTTModel, TreeForeignKey

from django.db import models
from django.urls import reverse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.db.models import F, Case, IntegerField, When, Value


class GetChildInstanceMixin:
    """
    Mixin for base model classes. Providing a method to get the child's
    instance.
    """
    def get_child_instance(self):
        """
        Return the instance of the child model class if possible. None
        otherwise.
        """
        for rel in self._meta.related_objects:
            # FIXME: Is this safe? Using parent_link on the remote field seems
            # not to work?!
            if isinstance(rel, models.OneToOneRel):
                try:
                    return getattr(self, rel.get_accessor_name())
                except rel.related_model.DoesNotExist:
                    continue
        return None


class HTMLMixin(GetChildInstanceMixin):
    """
    A mixin that provides a method to render the model instance as HTML using a
    template.
    """
    template_name = None

    def _get_base_type_name(self):
        """
        Return the base type name for this model. This is used to determine the
        template folder and the context variable name when rendering the template.
        """
        if isinstance(self, Page):
            return 'page'
        elif isinstance(self, Region):
            return 'region'
        elif isinstance(self, Section):
            return 'section'

    def get_template_name(self):
        """
        Return the template to use for this model. If template_name is set it
        will be used. If not the template name will be the class name as snake
        case. This method can be customized by child classes.
        """
        if self.template_name:
            return self.template_name
        else:
            # Cast class name to snake case for the template file name.
            cls = self.__class__
            template_name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
            return f'{self._get_base_type_name()}s/{template_name}.html'

    def render(self):
        """
        Render the model instance using its template and return the rendered
        HTML. This method can be customized by child classes.
        """
        template = get_template(self.get_template_name())
        return template.render({self._get_base_type_name(): self})

    @property
    def html(self):
        """
        Return the rendered HTML for this model instance.
        This property should not be overwritten by child classes. It just calls
        the render method, but tries to call the childs version of it.
        """
        return getattr(self.get_child_instance() or self, 'render')()


class ShowChildClassNameMixin(GetChildInstanceMixin):
    """
    A mixin that provides a __str__ method that shows the child class name if
    possible. This is useful for the admin interface to distinguish between
    different section types.
    """
    def __str__(self):
        child_instance = self.get_child_instance()
        if child_instance:
            return f"{child_instance.__class__.__name__}: {child_instance}"
        else:
            return super().__str__()


class Section(HTMLMixin, ShowChildClassNameMixin, models.Model):
    """
    A base model for content sections that can be added to pages.

    This model is ment as a base model for all section types, which can be any
    content type you want to see on your website. It does not contain any fields
    itself, but provides a common interface for rendering the section as HTML
    which can be customized by child classes.
    """


class Region(HTMLMixin, ShowChildClassNameMixin, models.Model):
    """
    A model for regions that can be added to pages.

    As a page a region is a container for sections to be rendered. This model is
    ment as a base model for specific region types like main oder sidebar. It
    does not contain any fields itself, but provides a common interface for
    rendering the region as HTML which can be customized by child classes.
    """


class Page(MPTTModel, ShowChildClassNameMixin, HTMLMixin):
    """
    A model holding everything to render a simple web page:
    - a slug for the URL for the page
    - the base page to create navigation menus
    - regions and sections to render the content of the page
    - a routine to get the template to render the page
    """

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )
    sections = models.ManyToManyField(
        Section,
        through="PageSection",
        related_name="pages",
        blank=True,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("page", kwargs={"slug": self.slug})

    def get_template(self):
        """
        Return the template to use for this page.

        First check if there is a template specific to this page's slug, then
        fall back to the default template.
        """
        try:
            get_template(f'pages/{self.slug}.html')
        except TemplateDoesNotExist:
            try:
                get_template('pages/page.html')
            except TemplateDoesNotExist:
                raise
            else:
                return 'pages/page.html'
        else:
            return f'pages/{self.slug}.html'


class OrderedRelationMixin:
    """
    This mixin provieds some logic to work with an ordered many-to-many
    relation. Such as recalculating the ordering when adding, removing or
    moving an item.
    """

    def _get_ordered_items(self):
        if hasattr(self, 'page'):
            kwargs = {'page': self.page}
        else:
            kwargs = {'region': self.region}
        return type(self).objects.filter(**kwargs)

    def delete_item(self):
        """
        Decrease index by one for all following items. Run this method after
        items was deleted.
        """
        items = self._get_ordered_items()
        for item in items.filter(index__gt=self.index):
            item.index -= 1
            item.save()

    def add_item(self):
        """
        Set max index + 1 for item. Run this method before item was saved.
        """
        items = self._get_ordered_items()
        max_index = items.aggregate(models.Max('index'))['index__max'] or 0
        self.index = max_index + 1

    def move_up_or_down(self, operation):
        items = self._get_ordered_items()
        index = self.index

        # Mysql does not allow us to switch indexes in one update statement
        # without unique constraint violation. So we set the indexes to its
        # negative value first.
        items.filter(index__in=[index, operation(index)]).update(index=-F('index'))
        items.filter(index__in=[-index, -operation(index)]).update(index=Case(
            When(index=-index, then=Value(operation(index))),
            When(index=-operation(index), then=Value(index)),
        ))

    def move_item_up(self):
        """
        Switch index with the index of the preceding item.
        """
        self.move_up_or_down(lambda i: i - 1)

    def move_item_down(self):
        """
        Switch index with the index of the following item.
        """
        self.move_up_or_down(lambda i: i + 1)


class RegionSection(OrderedRelationMixin, models.Model):
    """
    Ordered many-to-many relation between regions and sections.
    """

    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    index = models.SmallIntegerField(blank=True)

    class Meta:
        ordering = ["region__id", "index"]
        unique_together = (("region", "section"), ("region","index"))

    def __str__(self):
        return f"{self.region} — {self.section} ({self.index})"


class PageRegion(OrderedRelationMixin, models.Model):
    """
    Ordered many-to-many relation between pages and regions.
    """

    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    index = models.SmallIntegerField(blank=True)

    class Meta:
        ordering = ["page__id", "index"]
        unique_together = (("page", "region"), ("page","index"))

    def __str__(self):
        return f"{self.page} — {self.region} ({self.index})"


class PageSection(OrderedRelationMixin, models.Model):
    """
    Ordered many-to-many relation between pages and sections.
    """

    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    index = models.SmallIntegerField(blank=True)

    class Meta:
        ordering = ["page__id", "index"]
        unique_together = (("page", "section"), ("page","index"))

    def __str__(self):
        return f"{self.page} — {self.section} ({self.index})"
