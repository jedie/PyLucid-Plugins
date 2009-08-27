# coding: utf-8

import os

from pylucid.decorators import render_to

from gpx2googlemaps.gpx_parser import GPX_Parser
from gpx2googlemaps.preference_forms import Gpx2googlemapsPreferencesForm


@render_to("gpx2googlemaps/gpx.html")
def lucidTag(request, filename=None):
    """ insert language selector list into page """
    if filename is None:
        if request.user.is_staff:
            request.page_msg.error("lucidTag Error: 'filename' kwarg needed!")
        return "[GPX Error.]"

    if "." in filename or "/" in filename or "\\" in filename:
        if request.user.is_staff:
            request.page_msg.error("gpx filename wrong: Only filename, without path/extension allowed!")
        return "[GPX Error.]"

    pref_form = Gpx2googlemapsPreferencesForm()
    preferences = pref_form.get_preferences()
    google_key = preferences["google_key"]
    if not google_key:
        if request.user.is_staff:
            request.page_msg.error("Please insert your google API key into Gpx2googlemapsPreferencesForm!")
        return "[GPX Error.]"

    gpx_base_path = preferences["gpx_base_path"]

    filepath = gpx_base_path % filename

    if not os.path.isfile(filepath):
        if request.user.is_staff:
            request.page_msg.error("Path %r to gpx file wrong!" % filepath)
        return "[GPX Error.]"

    try:
        parser = GPX_Parser(filepath)
        #parser.parseTracks()
        #print parser.getTrack('ACTIVE LOG')
        parser.parse_waypoints()
    except:
        if request.user.is_staff:
            raise
        return "[GPX Error.]"

    context = {
        "google_key": google_key,
        "waypoints": parser.waypoints,
        "last_update": parser.last_update,
    }
    return context
