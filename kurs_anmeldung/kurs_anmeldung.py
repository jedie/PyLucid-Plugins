# -*- coding: utf-8 -*-

"""
    Kurs Anmeldung
    ~~~~~~~~~~~~~~


    Last commit info:
    ~~~~~~~~~
    $LastChangedDate: $
    $Rev: $
    $Author: JensDiemer $

    :copyleft: 2009 by Jens Diemer
    :license: GNU GPL v3 or above, see LICENSE for more details
"""

__version__= "$Rev: $"

from django import forms
from django.db import models
from django.core.mail import send_mail

from PyLucid.tools import crypt
from PyLucid.models import Page
from PyLucid.system.BasePlugin import PyLucidBasePlugin


# Don't send mails, display them only.
MAIL_DEBUG = True
#MAIL_DEBUG = False


#_____________________________________________________________________________
# models

class KursAnmeldung(models.Model):
    KURS_WAHL = (
        ("SS09 vormittags", "3dsmax - SS 2009 - Vormittags (9-12 Uhr)"),
        ("SS09 nachmittags", "3dsmax - SS 2009 - Nachmittags (13-16 Uhr)"),
    )
    WARTELISTE = (
        ("-", "Habe mich vorher noch nicht für diesen Kurs eingeschrieben."),
        ("SS07",    "SS 2007"),
        ("WS07/08", "WS 2007/2008"),
        ("SS08",    "SS 2008"),
        ("WS08/09", "WS 2008/2009"),
        (
            "unbekannt",
            "Hatte mich schon einmal eingetragen, weiß aber nicht mehr wann."
        ),
    )

    email = models.EmailField(
        verbose_name="Email", help_text="Deine gültige EMail Adresse.",
    )
    vorname = models.CharField(verbose_name="Vorname", max_length=128)
    nachname = models.CharField(verbose_name="Nachname", max_length=128)

    kurs_wahl = models.CharField(
        verbose_name="Kurs", help_text="",
        max_length=128, choices=KURS_WAHL,
    )

    semester = models.PositiveIntegerField(
        verbose_name="Semester", help_text="In welchem Semester bist du?",
    )
    matrikel_nr = models.PositiveIntegerField(
        verbose_name="Matrikel Nr.", help_text="Deine Matrikel Nummer",
        unique = True,
    )

    laptop = models.BooleanField(
        help_text="Kannst du einen Laptop mitbringen?"
    )

    warteliste = models.CharField(
        help_text= (
            "Stehst du schon in der Warteliste?"
            " In welchem Semester hattest du dich schon angemeldet?"
        ),
        max_length=128, choices = WARTELISTE,
    )

    ip_address = models.IPAddressField()
    verify_hash = models.CharField(max_length=128)
    verified = models.BooleanField(default=False)
    mail_sended = models.BooleanField()
    logging = models.TextField(help_text="For internal logging")

    createtime = models.DateTimeField(
        auto_now_add=True, help_text="Create time",
    )
    lastupdatetime = models.DateTimeField(
        auto_now=True, help_text="Time of the last change.",
    )

    def log(self, txt):
        now = datetime.datetime.now()
        self.logging += "%s - %s\n" % (now, txt)

    class Meta:
        app_label = 'PyLucidPlugins' # essential

# essential: a list of all plugin models:
PLUGIN_MODELS = (KursAnmeldung,)


class KursAnmeldungForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(KursAnmeldungForm, self).__init__(*args, **kwargs)

        # Change field meta data in a DRY way
        self.fields['semester'].min_value = 1
        self.fields['semester'].max_value = 30

        self.fields['matrikel_nr'].min_value = 10000
        self.fields['matrikel_nr'].max_value = 1000000

    class Meta:
        model = KursAnmeldung
        exclude=(
            'ip_address', 'verify_hash', 'verified', 'mail_sended', 'log',
            'createtime', 'lastupdatetime',
        )




class kurs_anmeldung(PyLucidBasePlugin):
    def lucidTag(self):
        if self.request.method == 'POST':
            form = KursAnmeldungForm(self.request.POST)
            self.page_msg(self.request.POST)
            if form.is_valid():
                # Create, but don't save the new instance.
                new_entry = form.save(commit=False)

                try:
                    new_entry.ip_address = self.request.META['REMOTE_ADDR']
                except Exception, err:
                    if self.request.debug:
                        raise
                    new_entry.log("Error getting ip: %s\n" % err)


                rnd_hash = crypt.get_new_seed()
                new_entry.verify_hash = rnd_hash

                try:
                    self._send_verify_email(rnd_hash)
                except Exception, err:
                    if self.request.debug:
                        raise
                    new_entry.mail_sended = False
                    new_entry.log("Error sending mail: %s" % err)
                else:
                    new_entry.mail_sended = True
                    new_entry.log("mail sended")

                # Save the new instance.
                new_entry.save()
        else:
            form = KursAnmeldungForm()

        context = {
            "form": form,
        }
        self._render_template("anmeldung", context)

    def _send_verify_email(self, verify_hash):
        """
        Send a verify email
        """
        verify_link = self.URLs.methodLink("verify", args=(verify_hash,))
        verify_link = self.URLs.make_absolute_url(reset_link)

        # FIXME: convert to users local time.
        now = datetime.datetime.now()

        email_context = {
            "verify_link": verify_link,

        }

        raw_recipient_list = self.preferences["notify"]
        recipient_list = raw_recipient_list.splitlines()
        recipient_list = [i.strip() for i in recipient_list if i]

        # Render the internal page
        emailtext = self._get_rendered_template(
            "verify_mailtext", email_context#, debug=2
        )

        send_mail_kwargs = {
            "from_email": settings.DEFAULT_FROM_EMAIL,
            "subject": "%s %s" % (settings.EMAIL_SUBJECT_PREFIX, mail_title),
#                from_email = sender,
            "recipient_list": recipient_list,
            "fail_silently": False,
        }

        if MAIL_DEBUG == True:
            self.page_msg("MAIL_DEBUG is on: No Email was sended!")
            self.page_msg(send_mail_kwargs)
            self.response.write("<fieldset><legend>The email text:</legend>")
            self.response.write("<pre>")
            self.response.write(emailtext)
            self.response.write("</pre></fieldset>")
            return
        else:
            send_mail(message = emailtext, **send_mail_kwargs)