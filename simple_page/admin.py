from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Page, PageSection
from .forms import ReorderRelationForm


class PageSectionInline(admin.TabularInline):
    form = ReorderRelationForm
    model = PageSection
    extra = 1
    fields = ("section", "index")


@admin.register(Page)
class PageAdmin(DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "slug")
    list_display_links=('indented_title',)
    list_filter = ("parent",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (PageSectionInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_subclasses()