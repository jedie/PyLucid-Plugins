#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    PyLucid GXP2GoogleMaps
    ~~~~~~~~~~~~~~~~~

    Last commit info:
    ~~~~~~~~~~~~~~~~~
    $LastChangedDate:  $
    $Rev: 1 $
    $Author: Thomas Wagner $

    :copyleft: 2009 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""
import sys

__author__ = "Thomas Wagner"
__license__ = "GNU General Public License (GPL)"
__url__ = "http://www.wathoserver.de"
__version__ = "$Rev$"


__version__ = "$Rev: 1 $"

from xml.dom import minidom
from cgi import escape, FieldStorage



class Waypoint:
    def __init__(self, node):
        self.name = node.getElementsByTagName('name')[0].firstChild.data.encode("iso-8859-15")
        self.desc = node.getElementsByTagName('desc')[0].firstChild.data
        self.lat = float(node.getAttribute('lat'))
        self.lon = float(node.getAttribute('lon'))
        self.sym = node.getElementsByTagName('sym')[0].firstChild.data
    def __str__(self):
        return str((self.name, self.desc))

class GPX_Parser:
    def __init__(self, filename):
        self.tracks = {}
        self.waypoints = []
        try:
            doc = minidom.parse(filename)
            doc.normalize()
	    self.last_update = doc.documentElement.getElementsByTagName('time')[0].firstChild.data
        except Exception, e:
            print e
            return # handle this properly later
        self.gpx = doc.documentElement

    def parse_tracks(self):
        for node in self.gpx.getElementsByTagName('trk'):
            self._parseTrack(node)

    def parse_waypoints(self):
        for node in self.gpx.getElementsByTagName('wpt'):
            #print node
            wpt = Waypoint(node)
            self.waypoints.append(wpt)

    def _parse_track(self, trk):
        name = trk.getElementsByTagName('name')[0].firstChild.data
        if not name in self.tracks:
            self.tracks[name] = {}
        for trkseg in trk.getElementsByTagName('trkseg'):
            for trkpt in trkseg.getElementsByTagName('trkpt'):
                lat = float(trkpt.getAttribute('lat'))
                lon = float(trkpt.getAttribute('lon'))
                ele = float(trkpt.getElementsByTagName('ele')[0].firstChild.data)
                rfc3339 = trkpt.getElementsByTagName('time')[0].firstChild.data
                self.tracks[name][rfc3339] = {'lat':lat, 'lon':lon, 'ele':ele}

    def getTrack(self, name):
        times = self.tracks[name].keys()
        #print times
        points = [self.tracks[name][time] for time in times.sort()]
        return [(point['lat'], point['lon']) for point in points]


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding("iso-8859-15")
    form = FieldStorage()
    base = form.getvalue('user', 'gc')
    print "Content-type: text/html;charset=utf-8"
    print
    parser = GPX_Parser('/home/%s/public_html/AllFound.gpx' % base)
    #parser.parseTracks()
    #print parser.getTrack('ACTIVE LOG')
    parser.parse_waypoints()
    #for wpt in parser.waypoints:
    #    print wpt
    parser.print_map()
