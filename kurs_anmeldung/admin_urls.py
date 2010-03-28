# coding: utf-8

"""
    PyLucid admin url patterns
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Last commit info:
    ~~~~~~~~~~~~~~~~~
    $LastChangedDate$
    $Rev$
    $Author:$

    :copyleft: 2009 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.conf.urls.defaults import patterns, url

from kurs_anmeldung import admin_views

urlpatterns = patterns('',
    url(r'^csv_export/$', admin_views.csv_export, name='KursAnmeldung-csv_export'),
    url(r'^get_emails/$', admin_views.get_emails, name='KursAnmeldung-get_emails'),
)

