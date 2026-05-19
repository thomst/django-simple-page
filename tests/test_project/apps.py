from django.apps import AppConfig


class TestProjectConfig(AppConfig):
    name = 'test_project'
    verbose_name = "Test Project"


    def ready(self):
        import test_project.renderer
