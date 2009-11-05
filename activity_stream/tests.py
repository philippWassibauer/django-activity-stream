import os, re
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from activity_stream.models import *
from activity_stream.templatetags.activity_stream_tags import users_activity_stream

import datetime

class StoryTest(TestCase):
    def setUp(self):
        self.file_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), "../../test_data")
        User.objects.get_or_create(username="admin", email="sfd@sdf.com")
        ActivityTypes.objects.create(name="placed", is_batchable=True)
        ActivityTypes.objects.create(name="placed2")
        
    def test_batching(self):
        c = Client()
        c.login(username='admin', password='localhost')
        photo = TestSubject.objects.create(test=True)
        photo.save()
        activityItem = create_activity_item("placed", User.objects.get(username="admin"), photo)
        self.assertTrue(activityItem)
        self.assertEquals(activityItem.is_batched, False)
        self.assertEquals(activityItem.subjects.count(), 1)

        activityItem2 = create_activity_item("placed", User.objects.get(username="admin"), photo)
        self.assertTrue(activityItem2)
        self.assertEquals(activityItem2.is_batched, True)
        self.assertEquals(activityItem2.subjects.count(), 2)


    def test_future_activities(self):
        c = Client()
        c.login(username='admin', password='localhost')
        photo = TestSubject.objects.create(test=False)
        photo.save()
        custom_date = datetime.date.today() + datetime.timedelta(3)
        activityItem = create_activity_item("placed2", User.objects.get(username="admin"), photo, custom_date=custom_date)
        self.assertTrue(activityItem)
        self.assertEquals(activityItem.is_batched, False)
        self.assertEquals(activityItem.subjects.count(), 1)
        items = users_activity_stream(User.objects.get(username="admin"),1000)
        self.assertEquals(len(items['activity_items']), 0)


