from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Page, Region, PageSection, PageRegion, RegionSection
from .forms import ReorderRelationForm


class PageSectionInline(admin.TabularInline):
    form = ReorderRelationForm
    model = PageSection
    extra = 1
    fields = ("section", "index")


class PageRegionInline(admin.TabularInline):
    form = ReorderRelationForm
    model = PageRegion
    extra = 1
    fields = ("region", "index")


class RegionSectionInline(admin.TabularInline):
    form = ReorderRelationForm
    model = RegionSection
    extra = 1
    fields = ("section", "index")


class BasePageAdmin(DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "slug")
    list_display_links=('indented_title',)
    list_filter = ("parent",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (PageSectionInline, PageRegionInline)


class BaseRegionAdmin(admin.ModelAdmin):
    inlines = (RegionSectionInline,)
