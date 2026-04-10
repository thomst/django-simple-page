from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Page, PageSection, Section


class PageSectionInline(admin.TabularInline):
    model = PageSection
    extra = 1
    fields = ("section", "order")
    ordering = ("order",)

    def order_view(self, obj):
        return obj.order
    order_view.short_description = "Order"
    order_view.admin_order_field = "order"


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    exclude = ("ordering", "order")
    list_display = ("title", "tree_view", "slug", "parent", "order", "ordering", "level")
    list_filter = ("parent",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (PageSectionInline,)

    def tree_view(self, obj):
        tree = obj.title
        if obj.level > 0:
            tree = "&nbsp;—&nbsp; " * obj.level + tree
        return mark_safe(tree)
    tree_view.short_description = "title"
    tree_view.admin_order_field = "title"