Getting started
###############

A full functional example project can be found here_.

.. _here: https://github.com/thomst/django-simple-page/tree/main/tests/test_project


Installation
============

Install `django-simple-page` using `pip`:

.. code-block:: bash

    pip install django-simple-page


Add `simple_page`, `reorder_items_widget` and `mptt` to your Django project's
`INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'django.contrib.admin',
        'simple_page',
        'reorder_items_widget',
        'mptt',
        'my_project',
        ...
    ]

Place them anywhere behind `django.contrib.admin` for template modifications to
work.


Setup your project
==================


Create a page model
-------------------

Simply subclass the simple_page's :class:`~.models.Page` model and setup its
regions. Use a proxy model if you don't have any need for additional model
fields:

.. code-block:: python

    from simple_page.models import Page

    class MyPage(Page):
        REGIONS = [
            ('main', 'Main Region'),
            ('sidebar', 'Sidebar'),
            ('footer', 'Footer'),
        ]

        class Meta:
            proxy = True


If you want to use a concrete page model with additional model fields, you can
do that. In that case use :class:`~.admin.BasePageAdmin` as a base class for its
modeladmin. See also the :doc:`admin integration docs <admin_integration>`.


Create some section models
--------------------------

Section models are always concrete child models of the :class:`~.models.Section`
class. Here are two examples for a text and images section:

.. code-block:: python

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


More informations about page and section models can be found
:doc:`here <pages_and_sections>`.


Create templates
----------------

Create your page template as 'templates/pages/my_page.html'. It might look
something like this:

.. code-block:: html

    {% load static simple_page %}

    <!DOCTYPE html>
    <html lang="en">

    <head>
        <title>{{ page.title }}</title>
        <link rel="stylesheet" href="{% static 'css/my_page.css' %}">
        {{ media }}
    </head>

    <body>
        <main>
            <h1>{{ page.title }}</h1>
            {% for section in main.sections %}
                {{ section.html }}
            {% endfor %}
        </main>
        <aside>
            <div class="nav">
                <nav>{% menu page max_level=2 include_root=True %}</nav>
            </div>
        </aside>
        <footer>
            {% for section in footer.sections %}
                {{ section.html }}
            {% endfor %}
        </footer>
    </body>


In this example we use the :func:`menu template tag <.templatetags.simple_page.menu>`
to build our navigation menu.

Create a template for your text section as 'templates/sections/text_section.html':

.. code-block:: html

    <div class="text-section">
        <h2>{{ section.title }}</h2>
        <p>{{ section.text }}</p>
    </div>


And a template for your image section as 'templates/sections/image_section.html':

.. code-block:: html

    <figure>
        <figcaption>{{ section.title }}</figcaption>
        <img src="{{ section.image.url }}" alt="{{ section.title }}">
    </figure>


See the :doc:`renderer docs <renderer>` for more details about how to name the
template files.


Create a custom renderer (optional)
-----------------------------------

Here is an example for a custom renderer to provide some extra css for your
image section:

.. code-block:: python

    from simple_page.renderer import SectionRenderer

    class ImageSectionRenderer(SectionRenderer):
        class Media:
            css = {
                'all': ('css/image_section.css',)
            }


Place it within a `renderers` module in your project and make sure it will be
imported. The best way to do that is in the `ready` method of your `AppConfig`
class:

.. code-block:: python

    from django.apps import AppConfig

    class MyProjectConfig(AppConfig):
        name = 'my_project'

        def ready(self):
            import my_project.renderers


See the :doc:`renderer docs <renderer>` for more details about custom renderer
classes.


Setup url configuration
-----------------------

Finally you need to setup your url configuration. Feel free to use the provided
:func:`page view function <.views.page_view>`:

.. code-block:: python

    from django.urls import path
    from simple_page.views import page_view

    urlpatterns = [
        path('<slug:slug>/', page_view, name='page'),
    ]


Finish
------

Now run :

.. code-block:: bash

    python manage.py makemigrations
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver


Login to the admin interface, create some pages and sections and visit your new
website!


.. note::

    The css files mentioned in the examples above are not covered by this
    documentation. You will need to style your website on your own.
