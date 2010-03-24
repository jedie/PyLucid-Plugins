#coding: utf-8

from django import forms

from external_plugins.kurs_anmeldung.models import Kurs, KursAnmeldung

class KursForm(forms.ModelForm):
    class Meta:
        model = Kurs


class KursAnmeldungForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        """ Change fields in a DRY way """
        super(KursAnmeldungForm, self).__init__(*args, **kwargs)

        # limit ModelMultipleChoiceField queryset and add only active entries
        self.fields['kurs_wahl'].queryset = Kurs.objects.filter(active=True)


    class Meta:
        model = KursAnmeldung
        exclude = (
            'ip_address', 'verify_hash', 'verified', 'mail_sended', 'logging',

            "besucht", "abgebrochen", "abgeschlossen",

            'createtime', 'lastupdatetime',
        )
