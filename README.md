# Welcome to django-simple-page

[<img src="https://github.com/thomst/django-simple-page/actions/workflows/ci.yml/badge.svg">](https://github.com/thomst/django-simple-page/)
[<img src="https://coveralls.io/repos/github/thomst/django-simple-page/badge.svg?branch=main">](https://coveralls.io/github/thomst/django-simple-page?branch=main)
[<img src="https://img.shields.io/badge/python-3-blue">](https://img.shields.io/badge/python-3-blue)
[<img src="https://img.shields.io/badge/django-3.2%20%7C%204.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1%20%7C%205.2%20%7C%206.0-orange">](https://img.shields.io/badge/django-3.2%20%7C%204.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1%20%7C%205.2%20%7C%206.0-orange)

A simple and straight forward cms build with django.

## Features

- **Hierarchical Pages**: Tree-structured pages using django-mptt.
- **Admin backend integration**: Everything handleable by django's admin backend.
- **Simple yet powerful concept**: Three basic elements: pages, regions and sections. Each customizable in all aspects.

## Description

The strength of this project is its simplicity. You have three elements to build
your web presentation with: pages, regions and sections. While pages hold
everything together, regions and sections are their building blocks.

### Pages

TODO

### Regions

TODO

### Sections

TODO


## Installation

1. Add `simple_page` to your Django project's `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    'simple_page',
    'mptt',  # Required for tree structure
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

## Usage

### Creating Content

1. **Pages**: Create hierarchical pages with slugs for URLs.
2. **Sections**: Extend the base `Section` model for different content types.
3. **Regions**: Use regions as containers for sections within pages.

### Example: Creating a Text Section

```python
from simple_page.models import Section

class TextSection(Section):
    content = models.TextField()

    def render(self):
        return f"<div>{self.content}</div>"
```

### Template Structure

Create templates in your project's template directories:

- `pages/page.html` - Default page template
- `regions/{region_type}.html` - Region templates
- `sections/{section_type}.html` - Section templates


## Models

### Core Models

- **Page**: Hierarchical pages with MPTT tree structure.
  - Fields: `title`, `slug`, `parent`, `sections` (M2M through PageSection)
  - Methods: `get_template()`, `get_absolute_url()`

- **Section**: Base model for content sections.
  - Extensible via mixins for rendering and child detection.

- **Region**: Base model for page regions (containers for sections).

### Through Models

- **PageSection**: Ordered many-to-many between pages and sections.
- **PageRegion**: Ordered many-to-many between pages and regions.
- **RegionSection**: Ordered many-to-many between regions and sections.


## License

This project is open source. See LICENSE file for details.