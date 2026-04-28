from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import PageSection


@receiver(pre_save, sender=PageSection)
def pre_save_page_section(sender, instance, **kwargs):
    # Ensure instance was added and not changed.
    if instance.pk is None:
        PageSection.objects.set_index(instance)


@receiver(post_delete, sender=PageSection)
def post_delete_page_section(sender, instance, **kwargs):
    PageSection.objects.update_indexes(instance)
