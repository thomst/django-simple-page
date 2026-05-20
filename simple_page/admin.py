"""
The admin integration for django-simple-page is realized by a customized page
modeladmin. This modeladmin is registered for the page model and will be used
for all proxy page models. It provides the following features:

- Let pages be orderable by drag and drop in the admin changelist view.
- Let the user choose the type of the page before rendering the page's add form.
- Set the initial value of the hidden page_type field in the page add form.
- Render an inline formset for each region of the page which allows to assign
  sections to the region and rearrange them via drag and drop.

For your own concrete page models you should use :class:`~.admin.BasePageAdmin`
as a base class for your modeladmin. It will take care of rendering the inline
formsets for regions and setting the appropriate value for the hidden page_type
field.
"""

from django.contrib import admin
from django.forms import HiddenInput
from django.utils.functional import cached_property
from django.utils.html import mark_safe
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from mptt.admin import DraggableMPTTAdmin
from .models import Page, PageSection
from .forms import ReorderRelationForm


class BaseRegionInline(admin.TabularInline):
    """
    Base inline for page sections. This inline is rendered for each region of a
    page. It uses a custom form to make the sections orderable via drag and
    drop within a region. For that we use the django-reorder-items-widget_.

    .. _django-reorder-items-widget: https://github.com/thomst/django-reorder-items-widget
    """
    region_name = None
    form = ReorderRelationForm
    model = PageSection
    extra = 1
    fields = ("section", "index", "region")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(region=self.region_name)

    class Media:
        js = ["simple_page/formset_handlers.js"]


class GetPageModelMixin:
    """
    A mixin to get the page model based on a page_type url query parameter or
    the page_type field of the current page object.
    """

    @cached_property
    def page_types(self):
        """
        Return content types of all page models.
        """
        exclude_apps = ["admin", "auth", "contenttypes", "sessions", "simple_page"]
        cts = ContentType.objects.exclude(app_label__in=exclude_apps)
        return [ct for ct in cts if ct.model_class() and issubclass(ct.model_class(), Page)]

    def get_page_model(self, request, obj=None):
        """
        Return the page model based on the request and object.
        """
        if obj:
            return obj.page_type.model_class()
        elif 'page_type' in request.GET:
            page_type_id = request.GET['page_type']
            try:
                page_type = [ct for ct in self.page_types if ct.id == int(page_type_id)][0]
            except (IndexError, ValueError):
                raise ValueError(f"Invalid page type id: {page_type_id}")
            else:
                return page_type.model_class()
        else:
            return self.model


class RenderPageRegionsMixin(GetPageModelMixin):
    """
    Render a :class:`~.models.PageSection` inline formset for each region of the
    page. Also make sure extra forms have the region's name as initial value for
    the region form field.
    """

    def get_page_regions(self, request, obj):
        return self.get_page_model(request, obj).get_regions()

    def get_formset_kwargs(self, request, obj, inline, prefix):
        kwargs = super().get_formset_kwargs(request, obj, inline, prefix)
        if isinstance(inline, BaseRegionInline):
             kwargs["initial"] = [
                {"region": inline.region_name}
                for i in range(inline.extra)
            ]
        return kwargs

    def get_inlines(self, request, obj):
        inlines = list(super().get_inlines(request, obj))
        regions = self.get_page_regions(request, obj)
        for region, title in regions:
            class_name = f"{region.capitalize()}Inline"
            attrs = dict(
                region_name=region,
                verbose_name=title,
                verbose_name_plural=title,
                )
            inlines.append(type(class_name, (BaseRegionInline,), attrs))
        return inlines


class ChoosePageTypeMixin(GetPageModelMixin):
    """
    Let the user choose the type of the page she wants to add. Therefore render
    a simple list of add-links which either set the page_type url-query
    parameter for proxy page models or link to the modeladmin changeform
    for concrete page models.
    """

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        # Set the title of the change form based on the page type.
        if add or change:
            title = _("Add %s") if add else _("Change %s")
        else:
            title = _("View %s")
        page_model = self.get_page_model(request, obj)
        context["title"] = title % page_model._meta.verbose_name
        return super().render_change_form(request, context, add, change, form_url, obj)

    def add_view(self, request, form_url="", extra_context=None):
        # Add page types to the context to render a list of add links for each
        # page type. Using their content type id in the query string.
        if "page_type" not in request.GET:
            extra_context = extra_context or {}
            extra_context["page_types"] = []
            for ct in self.page_types:
                name = ct.model_class()._meta.verbose_name
                if ct.model_class()._meta.proxy:
                    url = f"?page_type={ct.id}"
                else:
                    url = reverse(f"admin:{ct.app_label}_{ct.model}_add")
                extra_context["page_types"].append((url, name))
        return super().add_view(request, form_url, extra_context)


class SetPageTypeMixin(GetPageModelMixin):
    """
    Set the initial value of the hidden page_type field in changeforms when
    adding a new page.
    """

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        page_model = self.get_page_model(request, obj)
        form.base_fields["page_type"].initial = ContentType.objects.get_for_model(page_model)
        form.base_fields["page_type"].widget = HiddenInput()
        return form


@admin.register(Page)
class PageAdmin(SetPageTypeMixin, ChoosePageTypeMixin, RenderPageRegionsMixin, DraggableMPTTAdmin):
    """
    The modeladmin for all proxy page models. This modeladmin is already
    registered for the page model. It provides the following features:

    - Let pages be orderable by drag and drop in the admin changelist view.
    - Let the user choose the type of the page before rendering the page's add
      form.
    - Set the initial value of the hidden page_type field in the page add form.
    - Render an inline formset for each region of the page.
    """
    list_display = ("tree_actions", "indented_title", "slug", "page_type", "view_page_link")
    list_display_links=('indented_title',)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("parent",)

    def view_page_link(self, obj):
        url = obj.get_absolute_url()
        return mark_safe(f'<a href="{url}" target="_blank">View page</a>')
    view_page_link.short_description = "View page"


class BasePageAdmin(SetPageTypeMixin, RenderPageRegionsMixin, admin.ModelAdmin):
    """
    Base class for modeladmins for concrete page models. It provides the
    following features:

    - Set the initial value of the hidden page_type field in the page add form.
    - Render an inline formset for each region of the page.
    """
