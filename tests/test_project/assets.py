from simple_page import assets


class ExtraPageAssets(assets.Assets):
    css = {
        'all': ['test_project/extra_page.css']
    }
    js = ['test_project/extra_page.js']


class TextSectionAssets(assets.Assets):
    css = {
        'all': ['test_project/text_section.css']
    }
    js = ['test_project/text_section.js']
