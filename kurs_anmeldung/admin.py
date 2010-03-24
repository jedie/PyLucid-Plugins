# coding:utf-8

from django.contrib import admin
from django.conf import settings

from reversion.admin import VersionAdmin

from pylucid_project.apps.pylucid_admin.admin_site import pylucid_admin_site

from external_plugins.kurs_anmeldung.models import Kurs, KursAnmeldung


class KursAdmin(VersionAdmin):
    list_display = ("id", "name", "active", "site")
    list_display_links = ("name",)
    list_filter = ("active", "site")
    date_hierarchy = 'lastupdatetime'
    search_fields = ("name",)
    ordering = ('-lastupdatetime',)

pylucid_admin_site.register(Kurs, KursAdmin)



class KursAnmeldungAdmin(VersionAdmin):
    list_display = (
        "id",
#        "vorname", "nachname",
        "email", "verified", "kurs_wahl",
        "note", "log_html",
#        "laptop", "warteliste",
#        "createby", "lastupdateby",
    )
    list_display_links = ("id", "email",)
    list_filter = ("verified", "kurs_wahl", "laptop", "kurs_wahl", "warteliste", "createby", "lastupdateby",)
    date_hierarchy = 'lastupdatetime'
    search_fields = ("vorname", "nachname", "email", "note", "logging")
    ordering = ('-lastupdatetime',)

pylucid_admin_site.register(KursAnmeldung, KursAnmeldungAdmin)
