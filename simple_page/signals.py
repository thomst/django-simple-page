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
        instance.add_item()


pre_save.connect(set_index_on_adding, sender=PageSection)
pre_save.connect(set_index_on_adding, sender=PageRegion)
pre_save.connect(set_index_on_adding, sender=RegionSection)


def update_indexes_on_deleting(sender, instance, **kwargs):
    """
    Signal handler for post_delete on PageSection.

    Reorders remaining sections for the same page after deletion.
    """
    # Reorder remaining sections for this page
    instance.delete_item()


post_delete.connect(update_indexes_on_deleting, sender=PageSection)
post_delete.connect(update_indexes_on_deleting, sender=PageRegion)
post_delete.connect(update_indexes_on_deleting, sender=RegionSection)
