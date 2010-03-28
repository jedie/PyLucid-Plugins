# coding:utf-8

from django import http
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

from pylucid_project.utils.site_utils import get_site_preselection

from pylucid_project.apps.pylucid.decorators import check_permissions, render_to
from pylucid_project.apps.pylucid.markup.converter import apply_markup

from pylucid_project.apps.pylucid_admin.admin_menu import AdminMenu

from kurs_anmeldung.models import Kurs, KursAnmeldung

def install(request):
    """ insert PyLucid admin views into PageTree """
    output = []

    admin_menu = AdminMenu(request, output)
    menu_section_entry = admin_menu.get_or_create_section("Kurs Anmeldung")

    admin_menu.add_menu_entry(
        parent=menu_section_entry, url_name="KursAnmeldung-get_emails",
        name="get all emails", title="Get a list of all email addresses",
    )

    admin_menu.add_menu_entry(
        parent=menu_section_entry, url_name="KursAnmeldung-csv_export",
        name="csv export", title="csv export",
    )

    return "\n".join(output)


ALL_PERMISSIONS = (
    "kurs_anmeldung.add_kurs",
    "kurs_anmeldung.change_kurs",
    "kurs_anmeldung.delete_kurs",
    "kurs_anmeldung.add_kursanmeldung",
    "kurs_anmeldung.change_kursanmeldung",
    "kurs_anmeldung.delete_kursanmeldung",
)


@check_permissions(superuser_only=False, permissions=ALL_PERMISSIONS)
@render_to("kurs_anmeldung/get_emails.html")
def get_emails(request):
    queryset = KursAnmeldung.objects.all()
    queryset = queryset.filter(kurs_wahl__site=settings.SITE_ID)
    emails = queryset.values_list('email', flat=True)
    context = {
        "title": _("All emails"),
        "emails": emails,
    }
    return context

@check_permissions(superuser_only=False, permissions=ALL_PERMISSIONS)
@render_to("kurs_anmeldung/csv_export.html")
def csv_export(request):
#    data = []
    kurse = Kurs.on_site.filter(active=True)
#    for kurs in kurse:
#        anmeldungen = kurs.kurs_wahl.all()
#        data.append({
#            "kurs": kurs,
#            "anmeldungen": anmeldungen,
#        })

    context = {
        "title": _("CSV export"),
#        "data": data,
        "kurse": kurse,
    }
    return context
