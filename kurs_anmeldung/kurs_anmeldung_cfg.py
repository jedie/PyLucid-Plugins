# -*- coding: utf-8 -*-

#_____________________________________________________________________________
# meta information
__author__              = "Jens Diemer"
__url__                 = "http://www.PyLucid.org"
__description__         = "Kurs Anmeldung"
__long_description__ = """
usage: {% lucidTag kurs_anmeldung.get_register_link %}
"""
#_____________________________________________________________________________
# preferences

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from PyLucid.tools.forms_utils import ListCharField

f = forms.EmailField()
try:
    f.clean(settings.DEFAULT_FROM_EMAIL)
except forms.ValidationError, err:
    msg = (
        "Please change 'DEFAULT_FROM_EMAIL' in your settings.py,"
        " current value is: %s (Org.Error: %s)"
    ) % (settings.DEFAULT_FROM_EMAIL, err)
    raise AssertionError(msg)

class PreferencesForm(forms.Form):
    notify = forms.CharField(
        initial = "\n".join(
            [i["email"] \
            for i in User.objects.filter(is_superuser=True).values("email")]
        ),
        required=False,
        help_text = _(
            "Notify these email addresses if a new comment submited"
            " (seperated by newline!)"
        ),
        widget=forms.Textarea(attrs={'rows': '5'}),
    )
    from_email = forms.EmailField(
        initial = settings.DEFAULT_FROM_EMAIL,
        help_text = _("from witch email address should be send mails"),
    )
    email_subject = forms.CharField(
        initial = settings.EMAIL_SUBJECT_PREFIX + "Anmeldung",
        help_text=_("verify email subject")
    )
    link_title = forms.CharField(
        initial = "Anmeldung",
        help_text=_("Witch link title should be used?")
    )

#_____________________________________________________________________________
# plugin administration data

global_rights = {
    "must_login"    : False,
    "must_admin"    : False,
}

ADMIN_SECTION = u"Kurs Anmeldung"

plugin_manager_data = {
    "get_register_link" : global_rights,
    "register": global_rights,
    "notice": global_rights,
    "verify": global_rights,
    "administer": {
        "must_login"    : True,
        "must_admin"    : True,
        "admin_sub_menu": {
            "section"       : ADMIN_SECTION, # The sub menu section
            "title"         : "Anmeldungen verwalten",
            "help_text"     : "Verwalte die Anmeldungen für Kurse",
            "open_in_window": False, # Should be create a new JavaScript window?
            "weight" : 0, # sorting weight for every section entry
        },
    },
    "admin_kurs": {
        "must_login"    : True,
        "must_admin"    : True,
        "admin_sub_menu": {
            "section"       : ADMIN_SECTION, # The sub menu section
            "title"         : "Kurse verwalten",
            "help_text"     : "verwalten der Kurse",
            "open_in_window": False, # Should be create a new JavaScript window?
            "weight" : -5, # sorting weight for every section entry
        },
    },
    "toggle_kurs": {
        "must_login"    : True,
        "must_admin"    : True,
    },
}
