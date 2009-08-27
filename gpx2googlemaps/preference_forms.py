# coding: utf-8


from django import forms
from django.utils.translation import ugettext as _

from dbpreferences.forms import DBPreferencesBaseForm

class Gpx2googlemapsPreferencesForm(DBPreferencesBaseForm):
    gpx_base_path = forms.CharField(max_length=255, min_length=3,
        initial="pylucid_plugins/gpx2googlemaps/gpx_files/%s.gpx",
        help_text="Path to the gpx files. Insert one '%s' for filename."
    )
    google_key = forms.CharField(max_length=255, min_length=20, #?
        initial="",
        help_text="Your google API key."
    )

    class Meta:
        app_label = 'gpx2googlemaps'
