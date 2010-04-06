#coding:utf-8

from django.conf.urls.defaults import patterns, url, include

from pylucid_weave.views import url_info

urlpatterns = patterns('',
    url(r'', include('weave.urls')),
    url(r'^', url_info, name="weave-url_info"),
)
