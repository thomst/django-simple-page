from django.contrib import admin
from simple_page.admin import BasePageAdmin
from .models import TextSection, TextWithTitleSection
from .models import ExtraPage


@admin.register(TextSection)
class TextSectionAdmin(admin.ModelAdmin):
    pass


@admin.register(TextWithTitleSection)
class TextWithTitleSectionAdmin(admin.ModelAdmin):
    pass


@admin.register(ExtraPage)
class ExtraPageAdmin(BasePageAdmin):
    prepopulated_fields = {"slug": ("title",)}
