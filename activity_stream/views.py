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
from activity_stream.models import ActivityFollower, create_activity_item
from blog.models import Post,PostImage
from blog.forms import BlogForm, BlogImageForm

import datetime

def activity_stream_item(request, username, id, template_name="activity_stream/activity_item.html"):
    return render_to_response(template_name, {
        "search_terms": search_terms,
        "featured_post": featured_post,
        "blogposts": blogposts,
    }, context_instance=RequestContext(request))

@login_required
def start_follow(request, username, success_url=None):
    user = get_object_or_404(User, username=username)
    follower = ActivityFollower(to_user=user, from_user=request.user)
    follower.save()

    create_activity_item("started_following", request.user, user)

    if not success_url:
        success_url = reverse("profile_detail", args=(user.username,))
    return HttpResponseRedirect(success_url)

@login_required
def end_follow(request, username, success_url=None):
    user = get_object_or_404(User, username=username)
    follower = ActivityFollower.objects.get(to_user=user, from_user=request.user)
    follower.delete()
    if not success_url:
        success_url = reverse("activity_stream", args=(user.username,))
    return HttpResponseRedirect(success_url)

def like(request, id):
    user = get_object_or_404(User, username=username)
    return render_to_response(template_name, {
        "search_terms": search_terms,
        "featured_post": featured_post,
        "blogposts": blogposts,
    }, context_instance=RequestContext(request))


def activity_stream(request, username, template_name="activitystream/activity_stream.html"):
    user = get_object_or_404(User, username=username)
    return render_to_response(template_name, {
        "viewed_user": user,
    }, context_instance=RequestContext(request))

