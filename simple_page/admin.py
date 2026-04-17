from django.contrib import admin
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

    def get_inlines(self, request, obj):
        regions = self.get_regions(obj)
        inlines = list()
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
