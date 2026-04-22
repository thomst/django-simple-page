from django.forms import ModelForm, HiddenInput
from reorder_items_widget import ReorderItemsWidget


class ReorderRelationForm(ModelForm):
    """
    A ModelForm using the ReorderItemsWidget with an index field.
    """
    class Meta:
        widgets = {
            'index': ReorderItemsWidget(attrs={'class': 'hidden'}),
            'region': HiddenInput(),
        }


class PageForm(ModelForm):
    """
    A ModelForm for Page model.
    """
    class Meta:
        widgets = {"page_type": HiddenInput()}