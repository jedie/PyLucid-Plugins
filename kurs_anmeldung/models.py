# coding: utf-8

import datetime

from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.managers import CurrentSiteManager

from pylucid_project.apps.pylucid.models.base_models import AutoSiteM2M, UpdateInfoBaseModel


class Kurs(UpdateInfoBaseModel):
    """   
    e.g.:
    3dsmax - SS 2009 - Vormittags (9-12 Uhr)
    3dsmax - SS 2009 - Nachmittags (13-16 Uhr)

    inherited attributes from UpdateInfoBaseModel:
        createtime     -> datetime of creation
        lastupdatetime -> datetime of the last change
        createby       -> ForeignKey to user who creaded this entry
        lastupdateby   -> ForeignKey to user who has edited this entry
    """
    name = models.CharField(
        verbose_name="Kurs", help_text="Der Kursname",
        max_length=255, unique=True,
    )
    active = models.BooleanField(
        help_text="Ist der Kurs aktiv buchbar?"
    )

    site = models.ForeignKey(Site, editable=False, default=settings.SITE_ID)
    on_site = CurrentSiteManager('site')

    def __unicode__(self):
        return u"Kurs %s" % (self.name)

    class Meta:
        verbose_name_plural = "Kurse"



class KursAnmeldung(UpdateInfoBaseModel):
    """
    TODO: Hinzufügen von "Kursbesucht" oder so...
    
    inherited attributes from UpdateInfoBaseModel:
        createtime     -> datetime of creation
        lastupdatetime -> datetime of the last change
        createby       -> ForeignKey to user who creaded this entry
        lastupdateby   -> ForeignKey to user who has edited this entry
    """
    WARTELISTE = (
        ("-", "Habe mich vorher noch nicht für diesen Kurs eingeschrieben."),
        ("SS07", "SS 2007"),
        ("WS07/08", "WS 2007/2008"),
        ("SS08", "SS 2008"),
        ("WS08/09", "WS 2008/2009"),
        ("SS09", "SS 2009"),
        ("WS09/10", "WS 2009/2010"),
        (
            "unbekannt",
            "Hatte mich schon einmal eingetragen, weiß aber nicht mehr wann."
        ),
    )

    vorname = models.CharField(verbose_name="Vorname", max_length=128)
    nachname = models.CharField(verbose_name="Nachname", max_length=128)
    email = models.EmailField(
        verbose_name="Email", help_text="Deine gültige EMail Adresse.",
        #unique = True,
    )

    kurs_wahl = models.ForeignKey(Kurs, verbose_name="Kurs Wahl", related_name='kurs_wahl')

    besucht = models.BooleanField(help_text="Dieser Kurs wurde besucht.")
    abgebrochen = models.BooleanField(help_text="Dieser Kurs wurde besucht aber abgebrochen.")
    abgeschlossen = models.BooleanField(help_text="Dieser Kurs wurde besucht und abgeschlossen.")

    semester = models.PositiveIntegerField(
        verbose_name="Semester", help_text="In welchem Semester bist du?",
    )
    matrikel_nr = models.PositiveIntegerField(
        verbose_name="Matrikel Nr.", help_text="Deine Matrikel Nummer",
        #unique = True,
    )

    laptop = models.BooleanField(
        help_text="Kannst du einen Laptop mitbringen?"
    )

    warteliste = models.CharField(
        help_text=(
            "Stehst du schon in der Warteliste?"
            " In welchem Semester hattest du dich schon angemeldet?"
        ),
        max_length=128, choices=WARTELISTE,
    )
    note = models.TextField(
        null=True, blank=True,
        verbose_name="Anmerkung",
        help_text="Wenn du noch Fragen hast."
    )

    verify_hash = models.CharField(max_length=128)
    verified = models.BooleanField(default=False)
    mail_sended = models.BooleanField()
    logging = models.TextField(help_text="For internal logging")

    def clean_fields(self, exclude):
        """
        http://docs.djangoproject.com/en/dev/ref/models/instances/#django.db.models.Model.clean
        """
        message_dict = {}

        if "semester" not in exclude and self.semester > 30:
            message_dict["semester"] = ('Semester Wert scheint falsch zu sein.',)

        if "matrikel_nr" not in exclude and (self.matrikel_nr < 10000 or self.matrikel_nr > 1000000):
            message_dict["matrikel_nr"] = ('Die Matrikel Nummer scheint falsch zu sein.',)

        if message_dict:
            raise ValidationError(message_dict)

    def log(self, request, txt):
        now = datetime.datetime.utcnow()
        time_string = now.strftime("%Y-%m-%d %H:%M:%S")
        ip = request.META.get("REMOTE_ADDR", "???")
        self.logging += "\n%s %s %s" % (time_string, ip, txt)

    def log_html(self):
        """ for admin.ModelAdmin list_display """
        return "<br />".join(self.logging.splitlines())
    log_html.short_description = _('logging')
    log_html.allow_tags = True

    def __unicode__(self):
        return u"KursAnmeldung von %s %s" % (self.vorname, self.nachname)

    class Meta:
        unique_together = ("vorname", "nachname", "email")
        verbose_name_plural = "Kurs Anmeldungen"
