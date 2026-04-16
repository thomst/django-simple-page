from django.contrib import admin
from .models import TextSection
from .models import ImageSection


@admin.register(TextSection)
class TextSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "text")
    search_fields = ("title", "text")


@admin.register(ImageSection)
class ImageSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "image")
    search_fields = ("title",)
