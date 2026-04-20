from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
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


def get_page_types():
    cts = ContentType.objects.exclude(app_label="simple_page")
    return [ct for ct in cts if issubclass(ct.model_class(), Page)]


class GetPageModelMixin:
    def get_page_model(self, request, obj=None):
        if obj:
            return type(obj)
        elif 'page_type_id' in request.GET:
            page_type_id = request.GET['page_type_id']
            page_type = ContentType.objects.get_for_id(page_type_id)
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

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if "page_type_id" in request.GET:
            extra_context = extra_context or {}
            extra_context["page_type_name"] = self.get_page_model(request)._meta.verbose_name
        return super().changeform_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        page_types = get_page_types()

        if "page_type_id" not in request.GET:
            extra_context = extra_context or {}
            extra_context["page_types"] = [
                (ct.id, ct.model_class()._meta.verbose_name)
                for ct in page_types
                ]

        return super().add_view(request, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if not change:
            page_model = self.get_page_model(request)
            obj = page_model(**form.cleaned_data)
        obj.save()


@admin.register(Page)
class PageAdmin(ChoosePageTypeMixin, GetPageRegionsMixin, DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "slug")
    list_display_links=('indented_title',)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("parent",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_subclasses()
