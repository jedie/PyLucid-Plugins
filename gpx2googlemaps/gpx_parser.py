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


#class gpx2googlemaps(PyLucidBasePlugin):
#
#    def lucidTag(self):
#        self.display("0")
#
#    def display(self, function_info=None):
#        context = {}
#        self._render_template("display", context)#, debug=True)
#   

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

    def print_map(self):

        try:
            print u"""
            <script src="http://maps.google.com/maps?file=api&amp;v=2.x&amp;key=XXX" type="text/javascript"></script>
          <script language="javascript">
          function plus(element)
          {
             element.parentNode.children("plus").className="hidden";
             element.parentNode.children("small").className="hidden";
             element.parentNode.children("minus").className="visible";
             element.parentNode.children("large").className="visible";
          }
          function minus(element)
          {
             element.parentNode.children("plus").className="visible";
             element.parentNode.children("small").className="visible";
             element.parentNode.children("minus").className="hidden";
             element.parentNode.children("large").className="hidden";
          }
          function wheelevent(e)
          {
             if (!e) e = window.event;
             if (e.preventDefault) e.preventDefault();
             e.returnValue = false;
          }
          </script>
        
            """
            print u"""<html>
               <body onload="load()" onunload="GUnload()">
                <div id="map" style="width: 100%; height: 500px; position: relative; background-color: rgb(229, 227, 223);"></div>
          <script type='text/javascript'>
         
        
          function load() {
            if (GBrowserIsCompatible()) {
              function createMarker(point,markerOptions,Name) {
                var marker = new GMarker(point, markerOptions);
                GEvent.addListener(marker, "click", function() {
                  marker.openInfoWindowHtml(Name);
                });
                GEvent.addListener(marker,"mouseover", function() {
                  marker.openInfoWindowHtml(Name);
                });
                return marker;
              }
        
              var map = new GMap2(document.getElementById("map"));
              //var mgr = new MarkerManager(map);
	      map.setCenter(new GLatLng(50.00, 12.00), 13)
              map.addControl(new GLargeMapControl()); <!-- Adds zoom control -->
              map.addMapType(G_PHYSICAL_MAP);
              map.addControl(new GHierarchicalMapTypeControl());  <!-- Adds hybrid/street/satellite -->
              var gcIcon = new GIcon(G_DEFAULT_ICON);      
              gcIcon.image = "http://www.wathoserver.de/~gc/geocache-found.png";
              gcIcon.iconSize = new GSize(24,24);
              gcIcon.shadow="";
              gcIcon.iconAnchor = new GPoint(12,12);      
              gcIcon.infoWindowAnchor = new GPoint(24,0);
              markerOptions = { icon:gcIcon };
              var bounds = new GLatLngBounds();"""
            for wpt in self.waypoints:
                print u"""      
              var latlng = new GLatLng(%s, %s);      
              map.addOverlay(createMarker(latlng, markerOptions, '%s<hr/>%s<div><a href="http://www.geocaching.com/seek/cache_details.aspx?wp=%s" target="_blank">geocaching.com</a></div>'));
              bounds.extend(latlng)""" % (
                  wpt.lat, wpt.lon, escape(wpt.name, True), escape(wpt.desc, True), escape(wpt.name))
            print u"""        
              //map.setCenter(bounds.getCenter(), 11, G_HYBRID_MAP);
	      map.setCenter(bounds.getCenter())
              map.setZoom(map.getBoundsZoomLevel(bounds));
              map.enableScrollWheelZoom();     
            }
}
         //     GEvent.addDomListener(map, "DOMMouseScroll", wheelevent);
         // map.onmousewheel = wheelevent;
          
          
          </script>          
        <span class='last_update'>Letzte Aktualisierung: %s</span>""" % self.last_update
        except Exception, e:
            print e



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
