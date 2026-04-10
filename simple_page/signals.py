from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.db import models
from .models import PageSection


@receiver(pre_save, sender=PageSection)
def pagesection_pre_save(sender, instance, **kwargs):
    """
    Signal handler for pre_save on PageSection.

    Validates and prepares the instance before saving.
    """
    # Ensure order is a valid integer
    if instance.order is None or instance.order == '':
        page_sections = PageSection.objects.filter(page=instance.page)
        max_order = page_sections.aggregate(models.Max('order'))['order__max']
        instance.order = (max_order or -1) + 1


@receiver(post_delete, sender=PageSection)
def pagesection_post_delete(sender, instance, **kwargs):
    """
    Signal handler for post_delete on PageSection.

    Reorders remaining sections for the same page after deletion.
    """
    # Reorder remaining sections for this page
    remaining_sections = PageSection.objects.filter(page=instance.page).order_by('order')
    for idx, section in enumerate(remaining_sections):
        if section.order != idx:
            section.order = idx
            section.save()
