from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.db import models
from .models import PageSection, PageRegion, RegionSection


def set_index_on_adding(sender, instance, **kwargs):
    """
    Signal handler for adding orderable items.
    """
    # Ensure order is a valid integer
    if instance.index is None or instance.index == '':
        page_sections = PageSection.objects.filter(page=instance.page)
        instance.add_item(page_sections)


pre_save.connect(set_index_on_adding, sender=PageSection)
pre_save.connect(set_index_on_adding, sender=PageRegion)
pre_save.connect(set_index_on_adding, sender=RegionSection)


def update_indexes_on_deleting(sender, instance, **kwargs):
    """
    Signal handler for post_delete on PageSection.

    Reorders remaining sections for the same page after deletion.
    """
    # Reorder remaining sections for this page
    remaining_sections = PageSection.objects.filter(page=instance.page)
    instance.delete_item(remaining_sections)


post_delete.connect(update_indexes_on_deleting, sender=PageSection)
post_delete.connect(update_indexes_on_deleting, sender=PageRegion)
post_delete.connect(update_indexes_on_deleting, sender=RegionSection)
