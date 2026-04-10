import re

from django.db import models
from django.urls import reverse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist


class Section(models.Model):
    """
    A base model for content sections that can be added to pages.

    This model is designed to be extended by specific content types, such as
    text sections or image sections. It does not contain any fields itself,
    but provides a common interface and template resolution logic for all
    section types.
    """

    def __str__(self):
        # Get all reverse one-to-one relations and determine which child class
        # this instance belongs to.
        for rel in self._meta.related_objects:
            if isinstance(rel, models.OneToOneRel):
                try:
                    child_instance = getattr(self, rel.get_accessor_name())
                    return f"{child_instance.__class__.__name__}: {child_instance}"
                except rel.related_model.DoesNotExist:
                    continue
        # If no child instance is found, return a generic string representation.
        return f"{self.__class__.__name__} (ID: {self.id})"

    @classmethod
    def get_template(cls):
        """
        Return the template to use for this section.

        Look for a template named like the class name as snake case. If not
        found, raise a TemplateDoesNotExist error.
        """
        template_name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        try:
            get_template(f'sections/{template_name}.html')
        except TemplateDoesNotExist:
            raise
        else:
            return f'sections/{template_name}.html'

    def render(self):
        """
        Render the section using its template and return the rendered HTML.
        """
        template = get_template(self.get_template())
        return template.render({'section': self})


class Page(models.Model):
    """
    A model holding everything to render a simple web page:
    - a slug for the URL for the page
    - the base page to create navigation menus
    - sections to render the content of the page
    - a routine to get the template to render the page
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
    )
    order = models.IntegerField(blank=True)
    ordering = models.CharField(max_length=255, blank=True, unique=True)
    sections = models.ManyToManyField(
        Section,
        through="PageSection",
        related_name="pages",
        blank=True,
    )

    class Meta:
        ordering = ["ordering"]
        unique_together = ("parent", "order")

    def __str__(self):
        return self.title

    @property
    def ancestors(self):
        """
        Return a list of ancestor pages, starting with the top level parent.
        """
        ancestors = []
        page = self
        while page.parent:
            ancestors.append(page.parent)
            page = page.parent
        return list(reversed(ancestors))

    @property
    def level(self):
        """
        Return the level of this page in the page hierarchy, starting with 0
        for top level pages.
        """
        return len(re.findall(r'-', self.ordering))

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
