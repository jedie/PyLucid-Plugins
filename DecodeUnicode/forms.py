# coding: utf-8

"""
    PyLucid DecodeUnicode forms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~   

    Last commit info:
    ~~~~~~~~~
    $LastChangedDate:$
    $Rev:$
    $Author: JensDiemer $

    :copyleft: 2007-2010 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details
"""

from django import forms

from pylucid_project.pylucid_plugins.DecodeUnicode.unicode_data import unicode_block_data

class SlugValidationForm(forms.Form):
    block = forms.SlugField()

class SelectBlock(forms.Form):
    block = forms.ChoiceField(choices=unicode_block_data.get_choices())
