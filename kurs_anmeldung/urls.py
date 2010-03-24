# coding: utf-8

from django.conf.urls.defaults import patterns, url

from external_plugins.kurs_anmeldung import views

urlpatterns = patterns('',
#    url(r'^/tags/(?P<tags>.+?)/$', tag_view, name='Blog-tag_view'),
#    url(r'^/(?P<id>\d+?)/(?P<title>.*)/$', detail_view, name='Blog-detail_view'),
#
#    url(r'^/feed/(?P<tags>.+)/(?P<filename>.+?)$', feed, name='Blog-tag_feed'),
#    url(r'^/feed/(?P<filename>.+?)$', feed, name='Blog-feed'),

    url(r'^/verify_email/(?P<hash>.+?)/$', views.verify_email, name='KursAnmeldung-verify_email'),
    url(r'^', views.register, name='KursAnmeldung-register'),
)
