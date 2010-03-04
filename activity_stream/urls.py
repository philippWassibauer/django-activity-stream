from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^global-activity-stream/$', 'activity_stream.views.global_stream',
        name='global_activity_stream'),
    
    url(r'^ajax-global-activity-stream/$', 'activity_stream.views.global_stream',
            {"template_name":"activity_stream/ajax_global_stream.html"},
            name='ajax_global_activity_stream'),
    
    url(r'^(?P<username>[-\w]+)/(?P<id>[\d]+)/$',
         'activity_stream.views.activity_stream_item', name='activity_item'),
    
    url(r'^(?P<username>[-\w]+)/$', 'activity_stream.views.activity_stream',
        name='activity_stream'),
    
    url(r'^(?P<username>[-\w]+)/ajax$', 'activity_stream.views.following_stream',
        {"template_name":"activity_stream/ajax_following_stream.html"},
        name='ajax_following_stream'),
    
    url(r'^(?P<username>[-\w]+)/start-follow/$',
        'activity_stream.views.start_follow', name='start_activity_follow'),
    
    url(r'^(?P<username>[-\w]+)/end-follow/$',
         'activity_stream.views.end_follow', name='end_activity_follow'),
    
    url(r'^(?P<id>[\d]+)/like/$', 'activity_stream.views.like', name='activity_like'),
    
    
)
