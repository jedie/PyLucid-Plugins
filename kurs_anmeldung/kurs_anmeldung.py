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

import datetime

from django import forms
from django.db import models
from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.mail import SMTPConnection, EmailMessage

from PyLucid.tools import crypt
from PyLucid.models import Page
from PyLucid.system.BasePlugin import PyLucidBasePlugin


# Don't send mails, display them only.
#MAIL_DEBUG = True
MAIL_DEBUG = False


#_____________________________________________________________________________
# models

class Kurs(models.Model):
    """
    3dsmax - SS 2009 - Vormittags (9-12 Uhr)
    3dsmax - SS 2009 - Nachmittags (13-16 Uhr)
    """
    name = models.CharField(
        verbose_name="Kurs", help_text="Der Kursname",
        max_length=256, unique = True,
    )
    active = models.BooleanField(
        help_text="Ist der Kurs aktiv buchbar?"
    )

    createtime = models.DateTimeField(
        auto_now_add=True, help_text="Create time",
    )
    lastupdatetime = models.DateTimeField(
        auto_now=True, help_text="Time of the last change.",
    )

    def __unicode__(self):
        return u"Kurs %s" % (self.name)

    class Meta:
        app_label = 'PyLucidPlugins' # essential



class KursAnmeldung(models.Model):
    """
    TODO: Hinzufügen von "Kursbesucht" oder so...
    """
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
        #unique = True,
    )
    vorname = models.CharField(verbose_name="Vorname", max_length=128)
    nachname = models.CharField(verbose_name="Nachname", max_length=128)

    kurs_wahl = models.ManyToManyField(
        Kurs, related_name='kurs_wahl'
    )

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
        help_text= (
            "Stehst du schon in der Warteliste?"
            " In welchem Semester hattest du dich schon angemeldet?"
        ),
        max_length=128, choices = WARTELISTE,
    )
    note = models.TextField(
        null=True, blank=True,
        verbose_name="Anmerkung",
        help_text = "Wenn du noch Fragen hast."
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

    def __unicode__(self):
        return u"KursAnmeldung von %s %s" % (self.vorname, self.nachname)

    class Meta:
        app_label = 'PyLucidPlugins' # essential

# essential: a list of all plugin models:
PLUGIN_MODELS = (KursAnmeldung,Kurs)



class KursForm(forms.ModelForm):
    class Meta:
        model = Kurs


class KursAnmeldungForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        """ Change fields in a DRY way """
        super(KursAnmeldungForm, self).__init__(*args, **kwargs)

        self.fields['semester'].min_value = 1
        self.fields['semester'].max_value = 30

        self.fields['matrikel_nr'].min_value = 10000
        self.fields['matrikel_nr'].max_value = 1000000

        # add queryset to ModelMultipleChoiceField
        self.fields['kurs_wahl'].queryset=Kurs.objects.filter(active=True)


    class Meta:
        model = KursAnmeldung
        exclude=(
            'ip_address', 'verify_hash', 'verified', 'mail_sended', 'logging',
            'createtime', 'lastupdatetime',


        )





class kurs_anmeldung(PyLucidBasePlugin):

    def get_register_link(self):
        """ returns the link to the register form. """       
        # Get the preferences from the database:
        preferences = self.get_preferences()

        return u'<a href="%s">%s</a>' % (
            self.URLs.methodLink("register"), preferences["link_title"]
        )

    def register(self):
        """
        Important: This method must be called in a _command url!
        """
        if self.request.method == 'POST':
            form = KursAnmeldungForm(self.request.POST)
            #self.page_msg(self.request.POST)
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

                # Save the new instance.
                new_entry.save()

                # save many-to-many data
                form.save_m2m()

                self._send_verify_email(rnd_hash, new_entry)
                
                # Save new log entries
                new_entry.save()

                if MAIL_DEBUG != True:
                    url = self.URLs.methodLink("notice")
                    return HttpResponseRedirect(redirect_to = url)
        else:
            form = KursAnmeldungForm()

        if not Kurs.objects.filter(active=True):
            self.page_msg.red("Fehler: es gibt keine aktiven Kurse!")
            return

        context = {
            "url": self.URLs.methodLink("register"),
            "form": form,
        }
        self._render_template("anmeldung", context)

    def notice(self):
        """ after a user has send a valid form """
        self.context["PAGE"].title = u"Daten eingetragen"
        self._render_template("notice", {})

    def verify(self, path_info):
        """ check a email hash """
        try:
            hash = path_info.strip("/")
            entry = KursAnmeldung.objects.get(verify_hash=hash)
        except Exception, err:
            if self.request.debug:
                raise
            self.page_msg.red("URL error!")
            return
        
        if entry.verified == True:
            self.page_msg(u"Hinweis: Die Anmeldung ist schon bestätigt.")

        entry.verified = True
        entry.log("verified via email hash link")
        entry.save()

        context = {
            "entry": entry,
        }
        self._render_template("verified", context)

    def _send_verify_email(self, verify_hash, db_entry):
        """ Send a verify email """
        verify_link = self.URLs.methodLink("verify", args=(verify_hash,))
        verify_link = self.URLs.make_absolute_url(verify_link)

        # FIXME: convert to users local time.
        now = datetime.datetime.now()

        email_context = {
            "verify_link": verify_link,
            "db_entry": db_entry,
            "now": now,
        }

        # Get the preferences from the database:
        preferences = self.get_preferences()
        raw_notify_list = preferences["notify"]
        notify_list = raw_notify_list.splitlines()
        notify_list = [i.strip() for i in notify_list if i]

        # Render the internal page
        emailtext = self._get_rendered_template(
            "verify_mailtext", email_context, debug=MAIL_DEBUG
        )

        email_kwargs = {
            "from_email": preferences["from_email"],
            "subject": preferences["email_subject"],
            "body": emailtext,
            "to": [db_entry.email],
            "bcc": notify_list,
        }

        if MAIL_DEBUG == True:
            msg = u"MAIL_DEBUG is on: No Email was sended!"
            self.page_msg(msg)
            db_entry.log(msg)
            db_entry.mail_sended = False

            self.page_msg("django.core.mail.EmailMessage kwargs:")
            self.page_msg(email_kwargs)

            self.response.write("<fieldset><legend>The email text:</legend>")
            self.response.write("<pre>")
            self.response.write(emailtext)
            self.response.write("</pre></fieldset>")
            return

        # We can't use django.core.mail.send_mail, because all members
        # of the recipient list will see the others in the 'To' field.
        # But we would like to notify the admins via 'Bcc' field.

        connection = SMTPConnection(fail_silently = False)
        email = EmailMessage(**email_kwargs)

        try:
            sended = email.send(fail_silently = False)
        except Exception, err:
            if self.request.debug:
                raise
            db_entry.log("Error sending mail: %s" % err)
            db_entry.mail_sended = False
        else:
            db_entry.mail_sended = sended
            db_entry.log("mail sended: %s" % sended)

    #--------------------------------------------------------------------------

    def administer(self):
        kurse = Kurs.objects.all()
       
        items = KursAnmeldung.objects.all()
        anmeldungen = []
        for anmeldung in items:
            kurs_wahl = anmeldung.kurs_wahl.all()
            flat_kurs_wahl = sorted([kurs.name for kurs in kurs_wahl])
            
            kurs_wahl_bools = []
            for kurs in kurse:
                if kurs in kurs_wahl:
                    kurs_wahl_bools.append(True)
                else:
                    kurs_wahl_bools.append(False)
            
            anmeldungen.append({
                "db_instance": anmeldung,
                "kurs_wahl": kurs_wahl,
                "flat_kurs_wahl": flat_kurs_wahl,
                "kurs_wahl_bools": kurs_wahl_bools,
            })      
        
        context = {
            "anmeldungen": anmeldungen,
            "kurse": kurse,
        }
        self._render_template("administer", context)

    def admin_kurs(self):
        """ administrate Kurs entries """
        if self.request.method == 'POST':
            form = KursForm(self.request.POST)
            if form.is_valid():
                instance = form.save()
                self.page_msg.green("Kurs '%s' gespeichert!" % instance.name)
        else:
            form = KursForm()

        context = {
            "url": self.URLs.methodLink("admin_kurs"),
            "kurse": Kurs.objects.all(),
            "toggle": self.URLs.methodLink("toggle_kurs"),
            "form": form,
        }
        self._render_template("add_kurs", context)

    def toggle_kurs(self, path_info):
        """ toggle the Kurs activation Bool """
        kurs_id = path_info.strip("/")
        kurs = Kurs.objects.get(id=kurs_id)

        if kurs.active:
            kurs.active = False
        else:
            kurs.active = True

        kurs.save()

        self.page_msg.green("Kurs %s geändert." % kurs)

        # Display the list
        return self.admin_kurs()
