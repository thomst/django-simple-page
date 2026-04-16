from django.contrib import admin
from simple_page.admin import BasePageAdmin
from simple_page.admin import BaseRegionInline
from .models import TextSection
from .models import ImageSection
from .models import MainPage


@admin.register(TextSection)
class TextSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "text")
    search_fields = ("title", "text")


@admin.register(ImageSection)
class ImageSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "image")
    search_fields = ("title",)


@admin.register(MainPage)
class MainPageAdmin(BasePageAdmin):
    pass