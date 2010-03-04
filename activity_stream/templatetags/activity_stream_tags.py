from django.template import Library, Node, TemplateSyntaxError, TemplateDoesNotExist
from activity_stream.models import ActivityFollower, ActivityStreamItem, get_people_i_follow, get_my_followers
from django.template import Variable, resolve_variable
from django.template import loader
from django.db.models import get_model
from django import template

import datetime

register = Library()

@register.inclusion_tag("activity_stream/follower_list.html")
def followed_by_him(user, count):
    followed = get_people_i_follow(user, count)
    return {"followed": followed}

@register.inclusion_tag("activity_stream/following_list.html")
def following_him(user, count):
    fans = get_my_followers(user, count)
    return {"following": fans}


@register.inclusion_tag("activity_stream/user_activity_stream.html")
def users_activity_stream(user, count, offset=0):
	
	if not count:
		count = 20
		
	if not offset:
		offset=0
		
	activity_items = ActivityStreamItem.objects.filter(actor=user, 
						       subjects__isnull=False, 
						       created_at__lte=datetime.datetime.now()).order_by('-created_at').distinct()[offset:count]
	return {"activity_items": activity_items}


@register.inclusion_tag("activity_stream/friends_activity_stream.html")
def following_activity_stream(user, count, offset=0):
	
	if not count:
		count = 20
		
	if not offset:
		offset=0
		
	following =  get_people_i_follow(user, 1000)
	following = list(following)
	following.append(user)   
	activity_items = ActivityStreamItem.objects.filter(actor__in=following, subjects__isnull=False, created_at__lte=datetime.datetime.now()).order_by('-created_at').distinct()[offset:count]
	return {"activity_items": activity_items}


@register.inclusion_tag("activity_stream/global_activity_stream.html")
def global_activity_stream(count, offset=0, privacylevel=0):
	
	if not count:
		count = 20
		
	if not offset:
		offset=0
		
	activity_items = ActivityStreamItem.objects.filter(subjects__isnull=False,
						created_at__lte=datetime.datetime.now()).order_by('-created_at').distinct()[offset:count]
	
	return {"activity_items": activity_items}


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
