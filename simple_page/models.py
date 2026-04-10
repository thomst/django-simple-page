import re

from mptt.models import MPTTModel, TreeForeignKey

from django.db import models
from django.urls import reverse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist


class GetChildInstanceMixin:
    """
    Mixin for base model classes.
    """
    def get_child_instance(self):
        """
        Return the instance of the child model class if possible. None otherwise.
        """
        for rel in self._meta.related_objects:
            if isinstance(rel, models.OneToOneRel) and rel.remote_field.parent_link:
                try:
                    return getattr(self, rel.get_accessor_name())
                except rel.related_model.DoesNotExist:
                    continue
        return None

    def get_child_instance_or_self(self):
        """
        Return the instance of the child model class if possible. Return self
        otherwise.
        """
        return self.get_child_instance() or self


class HTMLMixin(GetChildInstanceMixin):
    """
    A mixin that provides a method to render the model instance as HTML using a
    template.
    """
    base_type_name = None

    def get_template_name(self):
        """
        Return the template to use for this model.
        By default the template name is the class name as snake case.
        """
        cls = self.__class__
        template_name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        return f'{cls.base_type_name}/{template_name}.html'

    def render(self):
        """
        Render the model instance using its template and return the rendered HTML.
        """
        template = get_template(self.get_template_name())
        return template.render({self.base_type_name: self})

    @property
    def html(self):
        """
        Return the rendered HTML for this model instance.
        This property should not be overwritten by child classes. It just calls
        the render method, but tries to call the childs version of it.
        """
        return getattr(self.get_child_instance_or_self(), 'render')()


class Section(HTMLMixin, models.Model):
    """
    A base model for content sections that can be added to pages.

    This model is designed to be extended by specific content types, such as
    text sections or image sections. It does not contain any fields itself,
    but provides a common interface and template resolution logic for all
    section types.
    """
    base_type_name = 'section'

    def __str__(self):
        # Get all reverse one-to-one relations and determine which child class
        # this instance belongs to.
        child_instance = self.get_child_instance()
        if child_instance:
            return f"{child_instance.__class__.__name__}: {child_instance}"
        else:
            super().__str__()


class Page(MPTTModel, HTMLMixin):
    """
    A model holding everything to render a simple web page:
    - a slug for the URL for the page
    - the base page to create navigation menus
    - sections to render the content of the page
    - a routine to get the template to render the page
    """
    base_type_name = 'page'

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

    # FIXME: Something like this might come with the mttp base model. So this
    # might be redundant.
    @property
    def base_page(self):
        """
        Return the top-level parent page for this page.

        If this page has no parent, return itself. The base page allows you to
        create navigation menus based on the top level page by looping through
        its children.
        """
        if self.parent:
            return self.parent.base_page
        else:
            return self


class PageSection(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    order = models.IntegerField(blank=True)

    class Meta:
        ordering = ["page__id", "order"]
        unique_together = (("page", "section"), ("page","order"))

    def __str__(self):
        return f"{self.page} — {self.section} ({self.order})"
