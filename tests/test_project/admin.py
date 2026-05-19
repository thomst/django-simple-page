from django.contrib import admin
from simple_page.admin import BasePageAdmin
from .models import TextSection
from .models import PageWithHeader


@admin.register(TextSection)
class TextSectionAdmin(admin.ModelAdmin):
    pass


@admin.register(PageWithHeader)
class PageWithHeaderAdmin(BasePageAdmin):
    prepopulated_fields = {"slug": ("title",)}
