from django.contrib import admin
from django.forms import HiddenInput
from django.utils.functional import cached_property
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from mptt.admin import DraggableMPTTAdmin
from .models import Page, PageSection
from .forms import ReorderRelationForm


class BaseRegionInline(admin.TabularInline):
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
    A mixin to choose the page model based on a page_type url query parameter or
    the the page_type field of the current page object.
    """

    @cached_property
    def page_types(self):
        """
        Return content types of all page models.
        """
        exclude_apps = ["admin", "auth", "contenttypes", "sessions", "simple_page"]
        cts = ContentType.objects.exclude(app_label__in=exclude_apps)
        return [ct for ct in cts if issubclass(ct.model_class(), Page)]

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
    Render a `PageSection` inline formset for each region of the page. Also make
    sure extra forms have the region's name as initial for the region field.
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
    parameter for proxy page models. Or use the page's own modeladmin change
    form for concrete page models.
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
    Be sure that change forms for adding pages have the correct page_type set.
    The page_type field will be hidden and equipped with an appropriate initial
    value.
    """

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        page_model = self.get_page_model(request, obj)
        form.base_fields["page_type"].initial = ContentType.objects.get_for_model(page_model)
        form.base_fields["page_type"].widget = HiddenInput()
        return form


@admin.register(Page)
class PageAdmin(SetPageTypeMixin, ChoosePageTypeMixin, RenderPageRegionsMixin, DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "slug", "page_type")
    list_display_links=('indented_title',)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("parent",)


class BasePageAdmin(SetPageTypeMixin, RenderPageRegionsMixin, admin.ModelAdmin):
    """
    Use this base class for your own concrete page modeladmin. It will take care
    of rendering an inline formset for each region. And set the appropriate
    value for the page_type field.
    """
