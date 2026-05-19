# Welcome to django-simple-page

[![Tests](https://github.com/thomst/django-simple-page/actions/workflows/tests.yml/badge.svg)](https://github.com/thomst/django-simple-page/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/thomst/django-simple-page/badge.svg?branch=main)](https://coveralls.io/github/thomst/django-simple-page?branch=main)
[<img src="https://img.shields.io/badge/django-3.2%20%7C%204.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1%20%7C%205.2%20%7C%206.0-orange">](https://img.shields.io/badge/django-3.2%20%7C%204.0%20%7C%204.1%20%7C%204.2%20%7C%205.0%20%7C%205.1%20%7C%205.2%20%7C%206.0-orange)

Django-simple-page is a cms buildkit for your website. The strength of this
project is its simplicity - using comprehensible yet powerful concepts. You get
the basic stuff, but retain all your freedom.

## Links

- [github](https://github.com/django-simple-page/)
- [docs](https://thomst.github.io/django-simple-page/)
- [pypi](https://pypi.org/project/django-simple-page/)


## Features

- **Tree structured Pages**: By django-mptt.
- **Pages, regions and sections**: Assigning sections to regions on pages.
- **Custom rendering logic**: Each page or section can have its own renderer.
- **Simple yet powerful concept**: Everything can be customized by subclassing.
- **Admin backend integration**: Easy to use. Order elements via drag and drop.


## Description

### Pages, regions and sections

You got a reliable database layout of pages and sections. Sections are
associated with regions on pages. Everything else is up to you. Sections could
be anything you want, from a simple content type like an article with title and
text body to a full featured gallery. You build what you need just by
subclassing the page and section model.

### Renderer

While there are default renderers for pages and sections which are probably
suitable for most use cases, you are free to completely adapt or overwrite them.
Each page or section can have its own renderer providing a specific rendering
logic. And each renderer can have its own Media class defining javascript or css
files. Those media assets are merged by the page renderer and be available as
`media` template variable.

### Admin integration

At least we provide a handy admin backend integration. Rearrange your pages by
drag and drop. Add sections to your page regions with inline formsets and
reorder them by just dragging them to their new position. It's simple and
sufficient.

### Summing-up

As you can see, everything is done by subclassing. While django-simple-page
giving you the basics to build your website, it is not taking any freedom from
you. You define your pages with regions, your sections as content, your
rendering logic with their media classes and put everything together like
building blocks.
