# coding: utf-8

from django.conf.urls.defaults import patterns, url

from pylucid_project.pylucid_plugins.DecodeUnicode.views import index, display_block


urlpatterns = patterns('',
    url(r'^/(?P<block_slug>.*)/$', display_block, name='DecodeUnicode-display_block'),
    url(r'^', index, name='DecodeUnicode-index'),
)
