from django.db import models

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField
from tagging.models import Tag

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from django.contrib.auth.models import User
from photologue.models import ImageModel



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
    batch_time_minutes = models.IntegerField(_("batch time in minutes"), null=True, blank=True)
    batch_template = models.TextField(_('batch template'), null=True, blank=True)
    is_batchable = models.BooleanField(default=False)
    def __unicode__(self):
        return self.name

def create_activity_item(type, user, subject, data=None, safetylevel=1, location=None):
    type = ActivityTypes.objects.get(name=type)
    if type.is_batchable:
        # see if one exists in timeframe
        batchable_items = ActivityStreamItem.objects.filter(actor=user, type=type).all()
        if batchable_items: # if no batchable items then just create a ActivityStreamItem below
            batchable_items[0].subjects.create(content_object=subject)
            batchable_items[0].is_batched = True
            batchable_items[0].save()
            return batchable_items[0]

    new_item = ActivityStreamItem.objects.create(actor=user, type=type, data=data, safetylevel=safetylevel,
                        location=location)
    new_item.subjects.create(content_object=subject)
    new_item.save()
    
    return new_item


class ActivityStreamItem(models.Model):
    SAFETY_LEVELS = (
        (1, _('Public')),
        (2, _('Followers')),
        (3, _('Friends')),
        (3, _('Private')),
    )
    actor          = models.ForeignKey(User, related_name="activity_stream")
    type            =  models.ForeignKey(ActivityTypes, related_name="segments", blank=True, null=True)

    data = SerializedDataField(_('data'), blank=True, null=True)

    safetylevel = models.IntegerField(_('safetylevel'), choices=SAFETY_LEVELS, default=2, help_text=_('Who can see this?'))
    created_at      = models.DateTimeField(_('created at'), default=datetime.now)

    location        = models.PointField(srid=4326, null=True, blank=True)
    location_name = models.CharField(_('location name'), max_length=300, blank=True)

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

    def render(self):
        from django.template.loader import get_template
        from django.template import Template
        from django.template import Context
        t = get_template('activity_stream/%s/full%s.html'%(self.type.name,self.get_batch_suffix()))
        html = t.render(Context({'activity_item': self}))
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
    activity_stream_item = models.ForeignKey(ActivityStreamItem, related_name="subjects")
    def __unicode__(self):
        return "%s %s"%(self.content_type, self.object_id)





