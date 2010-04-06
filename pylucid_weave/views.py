# coding:utf-8

"""
    glue plugin between pylucid <-> django-weave
"""

from django.core.urlresolvers import reverse
from django.http import Http404


def url_info(request):
    if request.user.is_anonymous():
        raise Http404

#    url = reverse("weave-url_info")
    url = request.build_absolute_uri()
    return "Please use url '%s' in your weave client settings." % url
