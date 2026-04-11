from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Page, PageSection, PageRegion


class PageSectionInline(admin.TabularInline):
    model = PageSection
    extra = 1
    fields = ("section", "index")
    ordering = ("index",)


class PageRegionInline(admin.TabularInline):
    model = PageRegion
    extra = 1
    fields = ("region", "index")
    ordering = ("index",)


@admin.register(Page)
class PageAdmin(DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "slug")
    list_display_links=('indented_title',)
    list_filter = ("parent",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (PageSectionInline, PageRegionInline)
