# coding: utf-8

"""
    PyLucid DecodeUnicode plugin
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~   

    Last commit info:
    ~~~~~~~~~
    $LastChangedDate:$
    $Rev:$
    $Author: JensDiemer $

    :copyleft: 2007-2010 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details
"""

__version__ = "$Rev:$"

import unicodedata

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from pylucid_project.apps.pylucid.decorators import render_to
from pylucid_project.pylucid_plugins.DecodeUnicode.forms import SlugValidationForm, SelectBlock
from pylucid_project.pylucid_plugins.DecodeUnicode.unicode_data import unicode_block_data

def lucidTag(request):
    msg = "[obsolete lucidTag DecodeUnicode]"
    if request.user.is_staff or settings.DEBUG:
        request.page_msg.error(
            "DecodeUnicode is a PluginPage,"
            " please remove lucidTag 'DecodeUnicode' tag / delete the page"
            " and create a new PluginPage!"
        )
    return msg

def index(request):
    block_slug = None

    if request.GET:
        form = SlugValidationForm(request.GET)
        if form.is_valid():
            block_slug = form.cleaned_data['block']
        else:
            msg = "Block unknown!"
            if request.user.is_staff or settings.DEBUG:
                msg += " (slug is invalid: %r)" % request.GET["block"]
            request.page_msg.error(msg)

    if block_slug is None:
        first_block = unicode_block_data.get_first_block()
        block_slug = first_block.slug

    url = reverse("DecodeUnicode-display_block", kwargs={"block_slug":block_slug})
    return HttpResponseRedirect(url)


@render_to("DecodeUnicode/display.html")
def display_block(request, block_slug):
    try:
        unicode_block = unicode_block_data[block_slug] # get a UnicodeBlock() instance
    except KeyError:
        msg = "Block unknown!"
        if request.user.is_staff or settings.DEBUG:
            msg += " (block slug: %r)" % block_slug
        request.page_msg.error(msg)
        return index(request)

    char_list = unicode_block.get_char_list()
    form = SelectBlock(initial={"block":block_slug})

    context = {
        "form": form,

        "prior_block": unicode_block_data.get_prior_block(unicode_block),
        "next_block": unicode_block_data.get_next_block(unicode_block),

        "block_name": unicode_block.name,

        "range_hex1": "0x%04X" % unicode_block.start,
        "range_hex2": "0x%04X" % unicode_block.end,

        "char_list": char_list,

        "unidata_version": unicodedata.unidata_version,
    }
    return context
