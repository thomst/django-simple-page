from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.db import models
from .models import Page, PageSection


@receiver(pre_save, sender=Page)
def set_page_order_and_ordering(sender, instance, **kwargs):
    """
    Signal handler to set the order and ordering fields for Page instances.
    """
    # Set order to the next available integer if not provided
    if instance.order is None or instance.order == '':
        siblings = Page.objects.filter(parent=instance.parent)
        max_order = siblings.aggregate(models.Max('order'))['order__max']
        instance.order = max_order + 1 if max_order is not None else 0

    # Set ordering to a string based on the order of each ancestor page.
    instance.ordering = "-".join(str(p.order) for p in instance.ancestors + [instance])


@receiver(post_delete, sender=Page)
def reorder_pages_after_delete(sender, instance, **kwargs):
    """
    Signal handler for post_delete on Page.

    Reorders remaining pages for the same parent after deletion.
    """
    # Reorder remaining pages for this parent
    try:
        parent = instance.parent
    except Page.DoesNotExist:
        parent = None
    remaining_pages = Page.objects.filter(parent=parent).order_by('order')
    for idx, page in enumerate(remaining_pages):
        if page.order != idx:
            page.order = idx
            page.save()


@receiver(pre_save, sender=PageSection)
def pagesection_pre_save(sender, instance, **kwargs):
    """
    Signal handler for pre_save on PageSection.

    Validates and prepares the instance before saving.
    """
    print('pre-save called for PageSection:', instance)
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
