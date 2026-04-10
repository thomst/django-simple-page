from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Page, PageSection


class PageSectionInline(admin.TabularInline):
    model = PageSection
    extra = 1
    fields = ("section", "order")
    ordering = ("order",)


@admin.register(Page)
class PageAdmin(DraggableMPTTAdmin):
    exclude = ("ordering", "order")
    list_display = ("tree_actions", "indented_title", "slug")
    list_display_links=('indented_title',)
    list_filter = ("parent",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (PageSectionInline,)
