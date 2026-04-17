from django.contrib import admin
from django.db.models import Max
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


class BasePageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "parent")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("parent",)

    def get_regions(self, obj):
        child_instance = Page.objects.get_subclass(id=obj.id)
        return getattr(child_instance, 'REGIONS', None) or [('main', 'Main Region')]

    def get_formset_kwargs(self, request, obj, inline, prefix):
        kwargs = super().get_formset_kwargs(request, obj, inline, prefix)
        if request.method != "POST" and isinstance(inline, BaseRegionInline):
            page_section = PageSection.objects.filter(page=obj, region=inline.region_name)
            max_index = page_section.aggregate(Max('index'))['index__max'] or -1
            kwargs["initial"] = [
                {"index": max_index + i + 1, "region": inline.region_name}
                for i in range(inline.extra)
            ]
        return kwargs

    def get_inlines(self, request, obj):
        inlines = list(super().get_inlines(request, obj))
        regions = self.get_regions(obj)
        for region, title in regions:
            class_name = f"{region.capitalize()}Inline"
            attrs = dict(
                region_name=region,
                verbose_name=title,
                verbose_name_plural=title,
                )
            inlines.append(type(class_name, (BaseRegionInline,), attrs))
        return inlines


@admin.register(Page)
class PageAdmin(BasePageAdmin, DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "slug")
    list_display_links=('indented_title',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_subclasses()
