from django.conf.urls.defaults import *

from blog import views, models
from blog.forms import *


urlpatterns = patterns('',
    # blog post
    url(r'^(?P<username>[-\w]+)/(?P<id>[\d]+)/$', 'activity_stream.views.activity_stream_item', name='activity_item'),
    url(r'^(?P<username>[-\w]+)/$', 'activity_stream.views.activity_stream', name='activity_stream'),
    url(r'^start-follow/(?P<username>[-\w]+)/$', 'activity_stream.views.start_follow', name='start_activity_follow'),
    url(r'^end-follow/(?P<username>[-\w]+)/$', 'activity_stream.views.end_follow', name='end_activity_follow'),

)
