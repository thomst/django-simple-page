from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Page, PageSection
from .forms import ReorderRelationForm


class PageSectionInline(admin.TabularInline):
    form = ReorderRelationForm
    model = PageSection
    extra = 1
    fields = ("section", "index")


class BasePageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "parent")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("parent",)

    def get_regions(self, obj):
        child_instance = Page.objects.get_subclass(id=obj.id)
        return getattr(child_instance, 'REGIONS', None) or ['main']

    def get_inlines(self, request, obj):
        regions = self.get_regions(obj)
        # Create PageSectionInline for each region.
        print(regions)
        return [PageSectionInline for r in regions]


@admin.register(Page)
class PageAdmin(BasePageAdmin, DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "slug")
    list_display_links=('indented_title',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_subclasses()
