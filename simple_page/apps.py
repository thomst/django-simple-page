from django.apps import AppConfig


class SimplePageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'simple_page'
    verbose_name = "Simple Page"


    def ready(self):
        import simple_page.signals
