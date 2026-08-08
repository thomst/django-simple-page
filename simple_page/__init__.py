"""
This is django-simple-page
==========================

Django-simple-page is a cms buildkit for your website. The strength of this
project is its simplicity - using comprehensible yet powerful concepts. You get
the basic stuff, but retain all your freedom.

Features
========

- **Tree structured Pages**: By django-mptt_.
- **Pages and sections**: Assigning sections to regions on pages.
- **Custom rendering logic**: Each page or section can have its own renderer.
- **Simple yet powerful concept**: Everything can be customized by subclassing.
- **Admin backend integration**: Easy to use via drag and drop.

.. _django-mptt: https://django-mptt.readthedocs.io/en/latest/


Basic Concept
=============

Pages and sections
------------------

You got a reliable database layout of :class:`pages <.models.Page>` and
:class:`sections <.models.Section>` objects. Sections are associated with
regions on pages. Everything else is up to you. Sections could be anything you
want, from a simple content type like an article with title and text body to a
full featured gallery. You build what you need just by subclassing the page and
section model.

Renderers
---------

Building HTML from pages and sections is done by :mod:`~.renderers`. While a
:class:`~.renderers.SectionRenderer` produces a html snippet representing the
section object, a :class:`~.renderers.PageRenderer` provides a full html
document - including all its sections. With a renderer class you can also define
media assets which are specific for a given page or section. Renderer classes
can be customized in any way - providing specific rendering logic for specific
page or section models.

Summing-up
----------

As you can see, everything is done by subclassing. While django-simple-page
giving you the basics to build your website, it is not taking any freedom from
you. You define your pages with regions, your sections as content, your
rendering logic with their media classes and put everything together like
building blocks.


Admin integration
=================

We provide a handy admin backend integration. Rearrange your pages by drag and
drop. Add sections to your page regions with inline formsets and reorder them by
just dragging them to their new position. It's simple and sufficient.


Utils
=====

Menu template tag
-----------------
We provide an inclusion template tag to generate a tree based menu using nested
lists. Still you are free to build your own menu logic or customize the default
menu template to your needs. See :func:`~.templatetags.simple_page.menu` for
more details.

Page view
---------
A simple view function to render a page by its slug. Use it in your url
configuration. See :func:`~.views.page_view` for more details.
"""