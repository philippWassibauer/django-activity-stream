from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.db import IntegrityError
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic import date_based
from django.conf import settings
from activity_stream.models import ActivityFollower, create_activity_item, ActivityStreamItem

import datetime
try:
    from notification import models as notification
except ImportError:
    notification = None

def activity_stream_item(request, username, id,
                         template_name="activity_stream/activity_item.html"):
    user = get_object_or_404(User, username=username)
    activity_item = get_object_or_404(ActivityStreamItem, pk=id)
    return render_to_response(template_name, {
        "activity_item": activity_item,
        "viewed_user": user,
    }, context_instance=RequestContext(request))

@login_required
def start_follow(request, username, success_url=None):
    user = get_object_or_404(User, username=username)
    follower = ActivityFollower(to_user=user, from_user=request.user)
    follower.save()

    create_activity_item("started_following", request.user, user)

    if not success_url:
        success_url = request.META.get('HTTP_REFERER','/')
       
    if notification:
        notification.send([user], "new_follower", {"follower": request.user})
        
    return HttpResponseRedirect(success_url)

@login_required
def end_follow(request, username, success_url=None):
    user = get_object_or_404(User, username=username)
    follower = ActivityFollower.objects.get(to_user=user, from_user=request.user)
    follower.delete()
    if not success_url:
        success_url = reverse("activity_stream", args=(user.username,))
    return HttpResponseRedirect(success_url)
    
    
@login_required
def like(request, id):
    subject = get_object_or_404(ActivityStreamItem, pk=id)
    create_activity_item("likes", request.user, subject)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))


def activity_stream(request, username, template_name="activity_stream/activity_stream.html"):
    user = get_object_or_404(User, username=username)
    return render_to_response(template_name, {
        "viewed_user": user,
        "count": request.GET.get("count", None),
        "offset": request.GET.get("offset", None),
    }, context_instance=RequestContext(request))


def global_stream(request, template_name="activity_stream/global_activity_stream.html"):
    return render_to_response(template_name, {
        "count": request.GET.get("count", None),
        "offset": request.GET.get("offset", None),
    }, context_instance=RequestContext(request))
    
    
def following_stream(request, username, template_name="activity_stream/following_stream.html"):
    user = get_object_or_404(User, username=username)
    return render_to_response(template_name, {
        "viewed_user": user,
        "count": request.GET.get("count", None),
        "offset": request.GET.get("offset", None),
    }, context_instance=RequestContext(request))


