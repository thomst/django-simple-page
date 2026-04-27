from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import PageSection


def update_indexes(sender, obj, **kwargs):
    PageSection.objects.filter(page=obj.page, region=obj.region).update_indexes(obj)


pre_save.connect(update_indexes, PageSection)
post_delete.connect(update_indexes, PageSection)
