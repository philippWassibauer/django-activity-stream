from django.db.models import signals
from django.utils.translation import ugettext_noop as _
import activity_stream.models
from activity_stream.models import ActivityTypes

try:
    from notification import models as notification
except ImportError:
    notification = None

    
def create_activity_types(app, created_models, verbosity, **kwargs):

    if notification:
        notification.create_notice_type("new_follower", _("New Follower"), _("somebody is following you now"), default=2)

    try:
        ActivityTypes.objects.create(name="started_following", batch_time_minutes=30, is_batchable=True)
    except:
        pass
    try:
        ActivityTypes.objects.create(name="likes", is_batchable=False)
    except:
        pass
signals.post_syncdb.connect(create_activity_types, sender=activity_stream.models)

