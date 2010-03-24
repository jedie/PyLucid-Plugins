# coding:utf-8

"""
    Kurs Anmeldung
    ~~~~~~~~~~~~~~


    Last commit info:
    ~~~~~~~~~
    $LastChangedDate: $
    $Rev: $
    $Author: JensDiemer $

    :copyleft: 2009-2010 by Jens Diemer
    :license: GNU GPL v3 or above, see LICENSE for more details
"""

__version__ = "$Rev: $"

import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.core.mail import SMTPConnection, EmailMessage
from django.template.loader import render_to_string

from pylucid_project.utils import crypt
from pylucid_project.apps.pylucid.decorators import render_to

from external_plugins.kurs_anmeldung.models import KursAnmeldung
from external_plugins.kurs_anmeldung.preference_forms import KursAnmeldungPrefForm
from external_plugins.kurs_anmeldung.forms import KursAnmeldungForm


# Don't send mails, display them only.
MAIL_DEBUG = True
#MAIL_DEBUG = False

@render_to("kurs_anmeldung/verified.html")
def verify_email(request, hash):
    """ check a email hash """
    try:
        entry = KursAnmeldung.objects.get(verify_hash=hash)
    except Exception, err:
        if settings.DEBUG:
            raise
        request.page_msg.red("URL error!")
        return

    if entry.verified == True:
        request.page_msg(u"Hinweis: Deine Anmeldung wurde bereits bestätigt.")

    entry.verified = True
    entry.log(request, "verified via email hash link")
    entry.save()

    context = {"entry": entry}
    return context


def _send_verify_email(request, preferences, db_entry, rnd_hash, new_entry):
    """ Send a verify email """

    location = reverse("KursAnmeldung-verify_email", kwargs={"hash":rnd_hash})
    verify_link = request.build_absolute_uri(location)

    # FIXME: convert to users local time.
    now = datetime.datetime.utcnow()

    email_context = {
        "verify_link": verify_link,
        "db_entry": db_entry,
        "now": now,
    }

    # Render the internal page
    emailtext = render_to_string("kurs_anmeldung/verify_mailtext.txt", email_context)

    # Get the preferences from the database:
    raw_notify_list = preferences["notify"]
    notify_list = raw_notify_list.splitlines()
    notify_list = [i.strip() for i in notify_list if i]

    email_kwargs = {
        "from_email": preferences["from_email"],
        "subject": preferences["email_subject"],
        "body": emailtext,
        "to": [db_entry.email],
        "bcc": notify_list,
    }

    if MAIL_DEBUG == True:
        msg = u"MAIL_DEBUG is on: No Email was sended!"
        request.page_msg(msg)
        db_entry.log(request, msg)
        db_entry.mail_sended = False

        request.page_msg("django.core.mail.EmailMessage kwargs:")
        request.page_msg(email_kwargs)

        request.page_msg("debug mail text:")
        request.page_msg(mark_safe("<pre>%s</pre>" % emailtext))
        return

    # We can't use django.core.mail.send_mail, because all members
    # of the recipient list will see the others in the 'To' field.
    # But we would like to notify the admins via 'Bcc' field.

    connection = SMTPConnection(fail_silently=False)
    email = EmailMessage(**email_kwargs)

    try:
        sended = email.send(fail_silently=False)
    except Exception, err:
        db_entry.log(request, "Error sending mail: %s" % err)
        db_entry.mail_sended = False
        if settings.DEBUG or request.user.is_staff:
            db_entry.save()
            raise
    else:
        db_entry.mail_sended = sended
        db_entry.log(request, "mail sended: %s" % sended)


@render_to()
def register(request):
    """
    Display the register form.
    """
    pref_form = KursAnmeldungPrefForm()
    preferences = pref_form.get_preferences()

    if request.method == 'POST':
        form = KursAnmeldungForm(request.POST)
        #self.page_msg(self.request.POST)
        if form.is_valid():
            # Create, but don't save the new instance.
            new_entry = form.save(commit=False)

            rnd_hash = crypt.get_new_seed()
            new_entry.verify_hash = rnd_hash

            new_entry.log(request, "created")

            # Save the new instance.
            new_entry.save()

            # save many-to-many data
            form.save_m2m()

            _send_verify_email(request, preferences, new_entry, rnd_hash, new_entry)

            # Save new log entries
            new_entry.save()

            context = {
                "template_name": "kurs_anmeldung/anmeldung_erfolgt.html",
                "title": preferences["title"],
            }
            return context
    else:
        form = KursAnmeldungForm()

    context = {
        "template_name": "kurs_anmeldung/anmeldung.html",
        "title": preferences["title"],
        "form": form,
    }
    return context


