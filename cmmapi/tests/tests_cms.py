#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import patch, Mock, MagicMock
from collections import namedtuple
from django.urls import reverse
from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from urllib.parse import parse_qs
from opaque_keys.edx.locator import CourseLocator
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.tests.factories import CourseEnrollmentAllowedFactory, UserFactory, CourseEnrollmentFactory
from common.djangoapps.student.auth import has_course_author_access
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from django.test.utils import override_settings
from cmmapi.serializers import CMMSerializer
from cmmapi.rest_api import CMMApi
from unittest.case import SkipTest
import re
import json
import urllib.parse


class TestCMMAPISerializers(ModuleStoreTestCase):
    def setUp(self):
        super(TestCMMAPISerializers, self).setUp()
        with patch('common.djangoapps.student.models.cc.User.save'):
            # staff user
            self.client = Client()
            self.user_staff = UserFactory(
                username='testuser3',
                password='12345',
                email='student2@edx.org',
                is_staff=True)
            self.client.login(username='testuser3', password='12345')

    def test_cmm_api_serializers(self):
        """
            test basic
        """
        body = {
            "name":'asd'
        }
        serializer = CMMSerializer(data=body)
        self.assertTrue(serializer.is_valid())

class TestCMMAPI(ModuleStoreTestCase):
    def setUp(self):
        super(TestCMMAPI, self).setUp()
        self.course = CourseFactory.create(
            org='mss',
            course='999',
            display_name='2022',
            emit_signals=True)
        aux = CourseOverview.get_from_id(self.course.id)
        with patch('common.djangoapps.student.models.cc.User.save'):
            self.student = UserFactory(
                username='student',
                password='12345',
                email='student@edx.org')
            self.student_2 = UserFactory(
                username='student2',
                password='12345',
                email='student2@edx.org')

    def test_cmm_api(self):
        """
            Test basic
        """
        body = {
            "name":'asd'
        }
        result = CMMApi().validate(body)
        self.assertTrue(result)
