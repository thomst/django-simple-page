# Welcome to django-simple-page

[![Tests](https://github.com/thomst/django-simple-page/actions/workflows/tests.yml/badge.svg)](https://github.com/thomst/django-simple-page/actions/workflows/tests.yml)
[<img src="https://coveralls.io/repos/github/thomst/django-simple-page/badge.svg?branch=main">](https://coveralls.io/github/thomst/django-simple-page?branch=main)
[<img src="https://img.shields.io/badge/django-3.2%20%7C%204.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1%20%7C%205.2%20%7C%206.0-orange">](https://img.shields.io/badge/django-3.2%20%7C%204.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1%20%7C%205.2%20%7C%206.0-orange)

A simple and straight forward cms buildkit for django.

## Features

- **Tree structured Pages**: By django-mptt.
- **Pages, regions and content**: Assigning content to regions on pages.
- **Admin backend integration**: Easy to use. Order elements via drag and drop.
- **Simple yet powerful concept**: Just gives you the basics, but leaving the freedom with you.

## Description

### Pages and sections

The strength of this project is its simplicity. You got a reliable database
layout of pages and sections. Sections are associated with regions on pages.
Everything else is up to you. Sections could be anything you want, from a simple
content type like an article with title and text body to a full featured
gallery. You build what you need just by subclassing the page and section model.

### Renderer

While there are default renderers for pages and sections which are probably
suitable for most use cases, you are free to completely adapt or overwrite them.
Each page or section can have its own renderer providing a specific logic.

### Assets

If there are any specific css or javascript files for your pages or sections,
simply sublcass the BaseAssets and register it with your page or section class.
The BaseAssets class is what you know from django as a Media class for forms.
And it is just as easy as that: defining js and css properties in the familiar
format.

### Summing-up

As you can see, everything is done by subclassing. While django-simple-pages
giving you the basics to build your website, it is not taking any freedom from
you. You define your pages with regions, your sections as content, your
rendering logic and your assets and put everything together like building
blocks.

Simple projects keep simple, while big projects keep their freedom. Be helpful,
but stay out of the way. That's what django-simple-pages wants to do.


## Installation

1. Add `simple_page` to your Django project's `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    'simple_page',
    'reorder_items_widget',
    'mptt',
]
```

2. Run migrations:

```bash
python manage.py migrate
```

3. Include the URLs in your project's `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    # ... other URLs
    path('', include('simple_page.urls')),
    path('admin/', admin.site.urls),
]
```
