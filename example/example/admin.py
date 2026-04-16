from django.contrib import admin
from simple_page.models import Page
from simple_page.admin import BasePageAdmin
from simple_page.admin import BaseRegionAdmin
from .models import TextSection
from .models import ImageSection
from .models import MainRegion
from .models import LeftSidebar


@admin.register(TextSection)
class TextSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "text")
    search_fields = ("title", "text")


@admin.register(ImageSection)
class ImageSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "image")
    search_fields = ("title",)


@admin.register(MainRegion)
class MainRegionAdmin(BaseRegionAdmin):
    pass


@admin.register(LeftSidebar)
class LeftSidebarAdmin(BaseRegionAdmin):
    pass


@admin.register(Page)
class PageAdmin(BasePageAdmin):
    pass
