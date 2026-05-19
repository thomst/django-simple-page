Getting started
###############

Installation
============

Install `django-simple-page` using `pip`::

    pip install django-simple-page


Add `simple_page`, `reorder_items_widget` and `mptt` to your Django project's
`INSTALLED_APPS`::

    INSTALLED_APPS = [
        ...
        'django.contrib.admin',
        ...
        'simple_page',
        'reorder_items_widget',
        'mptt',
        'my_project',
        ...
    ]

Take care of placing `simple_page` somewhere behind `django.contrib.admin`.


Setup
=====

Setup your page model
---------------------

Simply subclass the simple_page's :class:`~.models.Page` model and setup its
regions. Use a proxy model if you don't have any need for additional model
fields::

    from simple_page.models import Page

    class MyPage(Page):
        REGIONS = [
            ('main', 'Main Region'),
            ('sidebar', 'Sidebar'),
            ('footer', 'Footer'),
        ]

        class Meta:
            proxy = True


Setup some section models
-------------------------

Section models are always concrete child models of the :class:`~.models.Section`
class. Here are two examples for text blocks and images::

    from simple_page.models import Section

    class TextSection(Section):

        title = models.CharField(max_length=255)
        text = models.TextField(blank=True)

        def __str__(self):
            return self.title

    class ImageSection(Section):

        title = models.CharField(max_length=255)
        image = models.ImageField()

        def __str__(self):
            return self.title


Templates
---------

The default renderer looks for a template named like the model's class-name in
snake-case. And placed in a `pages` or `sections` folder - depending on what to
render.

We need at least three templates, one for the page, and one for each section.

TODO
