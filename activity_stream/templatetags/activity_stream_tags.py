from django.template import Library, Node, TemplateSyntaxError, TemplateDoesNotExist
from activity_stream.models import ActivityFollower, ActivityStreamItem, get_people_i_follow, get_my_followers
from django.template import Variable, resolve_variable
from django.template import loader
from django.db.models import get_model
from django import template

import datetime

register = Library()


@register.inclusion_tag("activity_stream/follower_list.html", takes_context=True)
def followed_by_him(context, user, count):
    followed = get_people_i_follow(user, count)
    return {"followed": followed, "request":context.get("request")}


@register.inclusion_tag("activity_stream/following_list.html", takes_context=True)
def following_him(context, user, count):
    fans = get_my_followers(user, count)
    return {"following": fans, "request":context.get("request")}


@register.inclusion_tag("activity_stream/user_activity_stream.html", takes_context=True)
def users_activity_stream(context, user, count, offset=0):
	if not count:
		count = 20
		
	if not offset:
		offset=0
	activity_items = ActivityStreamItem.objects.filter(actor=user, 
						       subjects__isnull=False, 
						       created_at__lte=datetime.datetime.now()).order_by('-created_at').distinct()[offset:count]
	return {"activity_items": activity_items, "user": context["user"],
		"request":context.get("request")}


@register.inclusion_tag("activity_stream/friends_activity_stream.html", takes_context=True)
def following_activity_stream(context, user, count, offset=0):
	
	if not count:
		count = 20
		
	if not offset:
		offset=0
	
	following =  get_people_i_follow(user, 1000)
	following = list(following)
	following.append(user)   
	activity_items = ActivityStreamItem.objects.filter(actor__in=following, subjects__isnull=False, created_at__lte=datetime.datetime.now()).order_by('-created_at').distinct()[offset:count]
	return {"activity_items": activity_items, "user": context["user"],
		"request":context.get("request")}


@register.inclusion_tag("activity_stream/global_activity_stream.html", takes_context=True)
def global_activity_stream(context, count, offset=0, privacylevel=0):
	
	if not count:
		count = 20
		
	if not offset:
		offset=0
		
	activity_items = ActivityStreamItem.objects.filter(subjects__isnull=False,
						created_at__lte=datetime.datetime.now()).order_by('-created_at').distinct()[offset:count]
	
	return {"activity_items": activity_items, "user": context["user"],
		"request":context.get("request")}


class RenderActivityNode(Node):
    def __init__(self, activity):
        self.activity = activity
        print self.activity
    
    def render(self, context):
        activity = context[self.activity]
        return activity.render(context)

def render_activity(parser, token):
    try:
        tag_name, format_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    return RenderActivityNode(format_string)

register.tag('render_activity', render_activity)


class IsFollowingNode(Node):
    def __init__(self, from_user, to_user, node_true, node_false):
        self.from_user = template.Variable(from_user)
        self.to_user = template.Variable(to_user)
        self.node_true = node_true
        self.node_false = node_false
        
    def render(self, context):
        to_user = self.to_user.resolve(context)
        from_user = self.from_user.resolve(context)
        if to_user and from_user:
            if to_user.is_authenticated() and from_user.is_authenticated():
                is_following = ActivityFollower.objects.filter(to_user=to_user, from_user=from_user).count()
                if is_following:
                    return self.node_true.render(context)
                else:
                    return self.node_false.render(context)
            else:
                return self.node_false.render(context)

def is_following(parser, token):
    bits = token.split_contents()[1:]
    nodelist_true = parser.parse(('else', 'endif_is_following'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endif_is_following',))
        parser.delete_first_token()
    else:
        nodelist_false = None
    return IsFollowingNode(bits[0], bits[1], nodelist_true, nodelist_false)

register.tag('if_is_following', is_following)
