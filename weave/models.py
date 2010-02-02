# coding:utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from pylucid_project.apps.pylucid.models.base_models import AutoSiteM2M, UpdateInfoBaseModel


class Collection(AutoSiteM2M, UpdateInfoBaseModel):
    """
    https://wiki.mozilla.org/Labs/Weave/Sync/1.0/Setup
       
    inherited attributes from AutoSiteM2M:
        sites   -> ManyToManyField to Site
        on_site -> sites.managers.CurrentSiteManager instance
    
    inherited attributes from UpdateInfoBaseModel:
        createtime     -> datetime of creation
        lastupdatetime -> datetime of the last change
        createby       -> ForeignKey to user who creaded this entry
        lastupdateby   -> ForeignKey to user who has edited this entry
    """
    user = models.ForeignKey(User)
    name = models.CharField(max_length=96)

    def __unicode__(self):
        return u"weave collection %r for user %r" % (self.name, self.user.username)


class Wbo(UpdateInfoBaseModel):
    """
    https://wiki.mozilla.org/Labs/Weave/Sync/1.0/API   
    https://wiki.mozilla.org/Labs/Weave/Sync/1.0/Setup
    
    inherited attributes from UpdateInfoBaseModel:
        createtime     -> datetime of creation
        lastupdatetime -> datetime of the last change
        createby       -> ForeignKey to user who creaded this entry
        lastupdateby   -> ForeignKey to user who has edited this entry
    """
    collection = models.ForeignKey(Collection)
    wboid = models.CharField(max_length=64, blank=True,
        help_text="wbo identifying string"
    )
    sortindex = models.IntegerField(null=True, blank=True,
        help_text="An integer indicting the relative importance of this item in the collection.",
    )
    payload = models.TextField(blank=True,
        help_text=(
            "A string containing a JSON structure encapsulating the data of the record."
            " This structure is defined separately for each WBO type. Parts of the"
            " structure may be encrypted, in which case the structure should also"
            " specify a record for decryption."
        )
    )

    def __unicode__(self):
        return u"weave wbo %r (%r)" % (self.wboid, self.collection)
