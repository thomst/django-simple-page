from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from mptt.admin import DraggableMPTTAdmin
from .models import Page, PageSection
from .forms import ReorderRelationForm, PageForm


class BaseRegionInline(admin.TabularInline):
    region_name = None
    form = ReorderRelationForm
    model = PageSection
    extra = 1
    fields = ("section", "index", "region")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(region=self.region_name)


class GetPageModelMixin:

    def get_page_model(self, request, obj=None):
        """
        Return the page model based on the request and object.
        """
        if obj:
            return obj.page_type.model_class()
        elif 'page_type' in request.GET:
            page_type = request.GET['page_type']
            page_type = ContentType.objects.get_for_id(page_type)
            return page_type.model_class()
        else:
            return self.model


class GetPageRegionsMixin(GetPageModelMixin):

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

    @staticmethod
    def get_page_types():
        """
        Return content types of all page models.
        """
        cts = ContentType.objects.exclude(app_label="simple_page")
        return [ct for ct in cts if issubclass(ct.model_class(), Page)]

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
            page_types = self.get_page_types()
            extra_context = extra_context or {}
            extra_context["page_types"] = [
                (ct.id, ct.model_class()._meta.verbose_name)
                for ct in page_types
                ]
        return super().add_view(request, form_url, extra_context)


@admin.register(Page)
class PageAdmin(ChoosePageTypeMixin, GetPageRegionsMixin, DraggableMPTTAdmin):
    form = PageForm
    list_display = ("tree_actions", "indented_title", "slug", "page_type")
    list_display_links=('indented_title',)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("parent",)
