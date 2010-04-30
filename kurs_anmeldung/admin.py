# coding:utf-8

from django.contrib import admin
from django.conf import settings

from reversion.admin import VersionAdmin

from external_plugins.kurs_anmeldung.models import Kurs, KursAnmeldung


class KursAdmin(VersionAdmin):
    list_display = ("id", "name", "active", "site")
    list_display_links = ("name",)
    list_filter = ("active", "site")
    date_hierarchy = 'lastupdatetime'
    search_fields = ("name",)
    ordering = ('-lastupdatetime',)

admin.site.register(Kurs, KursAdmin)



class KursAnmeldungAdmin(VersionAdmin):
    list_display = (
        "id",
        "vorname", "nachname", "kurs_wahl", "laptop", "warteliste",
        "email", "verified",
        "note", "log_html",
#        
#        "createby", "lastupdateby",
    )
    list_display_links = ("id", "email",)
    list_filter = ("verified", "kurs_wahl", "laptop", "kurs_wahl", "warteliste", "createby", "lastupdateby",)
    date_hierarchy = 'lastupdatetime'
    search_fields = ("vorname", "nachname", "email", "note", "logging")
    ordering = ('-lastupdatetime',)

admin.site.register(KursAnmeldung, KursAnmeldungAdmin)
