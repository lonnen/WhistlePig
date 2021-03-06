from django.conf import settings
from django.conf.urls.defaults import patterns, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .whistlepig import urls

from funfactory.monkeypatches import patch
patch()

# funfactory puts the more limited CompressorExtension extension in
# but we need the one from jingo_offline_compressor.jinja2ext otherwise we
# might an error like this:
#
#    AttributeError: 'CompressorExtension' object has no attribute 'nodelist'
#
from ical.ical_entries_feed import iCalEntriesFeed

from jingo_offline_compressor.jinja2ext import CompressorExtension
import jingo
try:
    jingo.env.extensions.pop(
        'compressor.contrib.jinja2ext.CompressorExtension'
    )
except KeyError:
    # happens if the urlconf is loaded twice
    pass
jingo.env.add_extension(CompressorExtension)

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'', include(urls)),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/statusupdate/sendoutagenotification/(?P<id>\d+)[/]$', 'whistlepig.admin_overrides.views.admin_send_outage_notification'),
    (r'^admin/', include(admin.site.urls)),
    (r'^browserid/', include('django_browserid.urls')),
    (r'^api[/]', include('whistlepig.api.urls')),
    #(r'^ical/feed/$', iCalEntriesFeed()),
    (r'^ical/feed/$', iCalEntriesFeed()),
)

## In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
