from django.db import models

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from django.contrib.auth.models import User

try:
    import cPickle as pickle
except:
    import pickle

import base64

# settings used by the app
ACTIVITY_DEFAULT_BATCH_TIME = getattr(settings, "ACTIVITY_DEFAULT_BATCH_TIME",
                                      30)

class SerializedDataField(models.TextField):
    """Because Django for some reason feels its needed to repeatedly call
    to_python even after it's been converted this does not support strings."""
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if value is None: return
        if not isinstance(value, basestring): return value
        value = pickle.loads(base64.b64decode(value))
        return value

    def get_db_prep_save(self, value):
        if value is None: return
        return base64.b64encode(pickle.dumps(value))


class ActivityFollower(models.Model):
    to_user  = models.ForeignKey(User, related_name="followed")
    from_user  = models.ForeignKey(User, related_name="following")
    created_at = models.DateTimeField(_('created at'), default=datetime.now)
    def __unicode__(self):
        return str(self.from_user)+" following "+str(self.to_user)
    class Meta:
        unique_together       = [('to_user', 'from_user')]
    
class ActivityTypes(models.Model):
    name  = models.CharField(_('title'), max_length=200, unique=True)
    template = models.TextField(_('template'), null=True, blank=True)
    batch_time_minutes = models.IntegerField(_("batch time in minutes"),
                                             null=True,
                                             blank=True)
    batch_template = models.TextField(_('batch template'), null=True, blank=True)
    is_batchable = models.BooleanField(default=False)
    def __unicode__(self):
        return self.name


class ActivityStreamItem(models.Model):
    SAFETY_LEVELS = (
        (1, _('Public')),
        (2, _('Followers')),
        (3, _('Friends')),
        (3, _('Private')),
    )
    actor = models.ForeignKey(User, related_name="activity_stream")
    type = models.ForeignKey(ActivityTypes, related_name="segments", blank=True,
                             null=True)

    data = SerializedDataField(_('data'), blank=True, null=True)

    safetylevel = models.IntegerField(_('safetylevel'), choices=SAFETY_LEVELS,
                                      default=2, help_text=_('Who can see this?'))
    created_at      = models.DateTimeField(_('created at'), default=datetime.now)

    is_batched = models.BooleanField(default=False)
    

    def first_subject(self):
        return self.subjects.all()[0]

    class Meta:
        get_latest_by       = '-created_at'

    def __unicode__(self):
        return str(self.actor)+" "+str(self.type)+" is_batched: %s"%self.is_batched

    def get_absolute_url(self):
        return ('activity_item', None, {
            'username': self.actor.username,
            'id': self.id
    })

    def render(self, context):
        from django.template.loader import get_template
        from django.template import Template
        from django.template import Context
        t = get_template('activity_stream/%s/full%s.html'%(self.type.name,self.get_batch_suffix()))
        html = t.render(Context({'activity_item': self,
                'request': context.get('request')}))
        return html
    get_absolute_url = models.permalink(get_absolute_url)
    
    def get_batch_suffix(self):
        if self.is_batched:
            return "_batched"
        else:
            return ""


class ActivityStreamItemSubject(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    activity_stream_item = models.ForeignKey(ActivityStreamItem,
                                             related_name="subjects")

    def __unicode__(self):
        return "%s %s"%(self.content_type, self.object_id)


from django.db.models.signals import post_save, post_delete
def delete_activity_on_subject_delete(sender, instance, **kwargs):
    if instance.activity_stream_item.subjects.count()<1:
        instance.activity_stream_item.delete()
post_delete.connect(delete_activity_on_subject_delete,
                    sender=ActivityStreamItemSubject)


def get_people_i_follow(user, count=20, offset=0):
    if hasattr(settings, "ACTIVITY_GET_PEOPLE_I_FOLLOW"):
        return settings.ACTIVITY_GET_PEOPLE_I_FOLLOW(user)
    else:
        followers =  ActivityFollower.objects.filter(from_user=user).all()[offset:count]
        return [follower.to_user for follower in followers]


def get_my_followers(user, count=20, offset=0):
    if hasattr(settings, "ACTIVITY_GET_MY_FOLLOWERS"):
        return settings.ACTIVITY_GET_MY_FOLLOWERS(user)
    else:
        followers = ActivityFollower.objects.filter(to_user=user).all()[offset:count]
        return [follower.from_user for follower in followers]


def create_activity_item(type, user, subject, data=None, safetylevel=1, custom_date=None):
    type = ActivityTypes.objects.get(name=type)
    if type.is_batchable:
        # see if one exists in timeframe
        batch_minutes = type.batch_time_minutes
        if not batch_minutes:
            batch_minutes = ACTIVITY_DEFAULT_BATCH_TIME

        cutoff_time = datetime.now()-timedelta(minutes=batch_minutes)
        batchable_items = ActivityStreamItem.objects.filter(actor=user, type=type,
                  created_at__gt=cutoff_time).order_by('-created_at').all()[0:1]
        if batchable_items: # if no batchable items then just create a ActivityStreamItem below
            batchable_items[0].subjects.create(content_object=subject)
            batchable_items[0].is_batched = True
            batchable_items[0].save()
            return batchable_items[0]

    new_item = ActivityStreamItem.objects.create(actor=user, type=type, data=data,
                                                 safetylevel=safetylevel)
    new_item.subjects.create(content_object=subject)
    
    if custom_date:
        new_item.created_at = custom_date
        new_item.save() 
    return new_item

    
from django.contrib.contenttypes import generic
class TestSubject(models.Model):
    test = models.BooleanField(default=False)
    activity = generic.GenericRelation(ActivityStreamItemSubject)
