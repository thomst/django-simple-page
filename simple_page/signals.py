from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import PageSection


@receiver(pre_save, sender=PageSection)
def set_index_on_adding(sender, instance, **kwargs):
    """
    Signal handler for adding orderable items.
    """
    # Ensure instance was added (not changed) and has no index value
    if instance.pk is None and instance.index is None:
        instance.update_indexes_on_adding()


@receiver(post_delete, sender=PageSection)
def update_indexes_on_deleting(sender, instance, **kwargs):
    """
    Signal handler for post_delete on PageSection.

    Reorders remaining sections for the same page after deletion.
    """
    # Reorder remaining sections for this page
    instance.update_indexes_on_deleting()
