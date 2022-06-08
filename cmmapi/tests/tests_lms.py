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
from lms.djangoapps.instructor_task.tasks_helper.enrollments import upload_students_csv
from lms.djangoapps.instructor_task.models import InstructorTask, ReportStore
from django.test.utils import override_settings
from cmmapi.serializers import CMMCourseSerializer, CMMProblemSerializer
from cmmapi.utils import get_students_features, get_status_tasks, export_ora2_data, get_problem_responses, get_students_roles
from cmmapi.task import generate
from unittest.case import SkipTest
from uuid import uuid4
import re
import json
import urllib.parse


class TestCMMAPISerializers(ModuleStoreTestCase):
    def setUp(self):
        super(TestCMMAPISerializers, self).setUp()
        self.course = CourseFactory.create(
            org='mss',
            course='999',
            display_name='2022',
            emit_signals=True)
        aux = CourseOverview.get_from_id(self.course.id)
        with patch('common.djangoapps.student.models.cc.User.save'):
            # staff user
            self.client = Client()
            self.user_staff = UserFactory(
                username='testuser3',
                password='12345',
                email='student2@edx.org',
                is_staff=True)
            self.client.login(username='testuser3', password='12345')

    def test_cmm_api_course_serializers(self):
        """
            test course serializers
        """
        body = {
            "course_id":str(self.course.id)
        }
        serializer = CMMCourseSerializer(data=body)
        self.assertTrue(serializer.is_valid())
    
    def test_cmm_api_block_serializers(self):
        """
            test block serializers
        """
        body = {
            "block_id": 'block-v1:eol+test+2022+type@html+block@693c0c6a47h54bd7a52ee9bad58da0fb'
        }
        serializer = CMMProblemSerializer(data=body)
        self.assertTrue(serializer.is_valid())

    def test_cmm_api_course_serializers_no_exists(self):
        """
            test course serializers when course dont exists
        """
        body = {
            "course_id":'course-v1:eol+Test101+2021'
        }
        serializer = CMMCourseSerializer(data=body)
        self.assertFalse(serializer.is_valid())
    
    def test_cmm_api_course_serializers_no_params(self):
        """
            test course serializers when there is not data in body post
        """
        body = {}
        serializer = CMMCourseSerializer(data=body)
        self.assertFalse(serializer.is_valid())
    
    def test_cmm_api_block_serializers_wrong(self):
        """
            test block serializers when block id is wrong
        """
        body = {
            "block_id": 'asdasdsadsadasdd'
        }
        serializer = CMMProblemSerializer(data=body)
        self.assertFalse(serializer.is_valid())

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
                email='student@edx.org',
                is_staff=True)
            self.student_2 = UserFactory(
                username='student2',
                password='12345',
                email='student2@edx.org')

    @patch("cmmapi.utils.submit_task")
    def test_cmm_api_student_profile(self, mock_submit):
        """
            test student profile report has been generated
        """
        mock_submit.side_effect = [namedtuple("Task",["task_id",])('123-456-789',),]
        result = get_students_features(Mock(), str(self.course.id))
        success_status = 'El reporte Perfil de estudiantes está siendo creado.'
        expected = {"status": success_status, 'task_id': '123-456-789'}
        self.assertEqual(expected, result)
    
    @patch("cmmapi.utils.submit_task")
    def test_cmm_api_ora2(self, mock_submit):
        """
            test ora2 report has been generated
        """
        mock_submit.side_effect = [namedtuple("Task",["task_id",])('123-456-789',),]
        result = export_ora2_data(Mock(), str(self.course.id))
        success_status = 'El reporte ORA2 está siendo creado.'
        expected = {"status": success_status, 'task_id': '123-456-789'}
        self.assertEqual(expected, result)
    
    @patch("cmmapi.utils.submit_task")
    def test_cmm_api_problem(self, mock_submit):
        """
            test problem report has been generated
        """
        mock_submit.side_effect = [namedtuple("Task",["task_id",])('123-456-789',),]
        result = get_problem_responses(Mock(), 'block-v1:eol+test+2022+type@html+block@693c0c6a47h54bd7a52ee9bad58da0fb')
        success_status = 'El reporte Problem Responses está siendo creado.'
        expected = {"status": success_status, 'task_id': '123-456-789'}
        self.assertEqual(expected, result)

    @patch("cmmapi.task.submit_task")
    def test_cmm_api_user_roles(self, mock_submit):
        """
            test users role report has been generated
        """
        mock_submit.side_effect = [namedtuple("Task",["task_id",])('123-456-789',),]
        result = get_students_roles(Mock(), str(self.course.id))
        success_status = 'El reporte Rol Usuarios está siendo creado.'
        expected = {"status": success_status, 'task_id': '123-456-789'}
        self.assertEqual(expected, result)
    
    def test_cmm_api_task_status(self):
        """
            test list task
        """
        query_features = ['id', 'username', 'name', 'email',]
        with patch('lms.djangoapps.instructor_task.tasks_helper.runner._get_current_task'):
            result = upload_students_csv(None, None, self.course.id, query_features, 'calculated')
        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        links = report_store.links_for(self.course.id)
        output = {"report_name": links[0][0]}
        task_1 = InstructorTask.objects.create(
                course_id=self.course.id,
                task_id=str(uuid4()),
                task_type='cmmapi_profile_info_csv',
                task_key="CMM-API-STUDENT-PROFILE-{}".format(str(self.course.id)),
                task_input='{}',
                task_state='SUCCESS',
                task_output=json.dumps(output),
                requester=self.student,
            )
        task_2 = InstructorTask.objects.create(
                course_id=self.course.id,
                task_id=str(uuid4()),
                task_type='cmmapi_profile_info_csv',
                task_key="CMM-API-STUDENT-PROFILE-{}".format(str(self.course.id)),
                task_input='{}',
                task_state='PROGRESS',
                task_output='{}',
                requester=self.student,
            )
        list_task = get_status_tasks(str(self.course.id))
        expect = [{'task_type': task_1.task_type, 'task_id': task_1.task_id, 'task_state': task_1.task_state, 'task_output': task_1.task_output, 'url': links[0][1]},
            {'task_type': task_2.task_type, 'task_id': task_2.task_id, 'task_state': task_2.task_state, 'task_output': task_2.task_output}]
        self.assertEqual(expect, list_task['list_task'])

class TestCMMAPI_UserRole(ModuleStoreTestCase):
    def setUp(self):
        super(TestCMMAPI_UserRole, self).setUp()
        self.course = CourseFactory.create(
            org='mss',
            course='999',
            display_name='2021',
            emit_signals=True)
        aux = CourseOverview.get_from_id(self.course.id)
        with patch('common.djangoapps.student.models.cc.User.save'):
            # staff user
            self.user_instructor = UserFactory(
                username='instructor',
                password='12345',
                email='instructor@edx.org',
                is_staff=True)
            CourseEnrollmentFactory(
                user=self.user_instructor, course_id=self.course.id, mode='honor')
            role = CourseInstructorRole(self.course.id)
            role.add_users(self.user_instructor)
            self.student = UserFactory(
                username='student',
                password='test',
                email='student@edx.org')
            # Enroll the student in the course
            CourseEnrollmentFactory(
                user=self.student, course_id=self.course.id, mode='honor')

    def _verify_csv_file_report(self, report_store, expected_data):
        """
            Verify course survey data.
        """
        report_csv_filename = report_store.links_for(self.course.id)[0][0]
        report_path = report_store.path_to(self.course.id, report_csv_filename)
        with report_store.storage.open(report_path) as csv_file:
            csv_file_data = csv_file.read()
            # Removing unicode signature (BOM) from the beginning
            csv_file_data = csv_file_data.decode("utf-8-sig")
            for data in expected_data:
                self.assertIn(data, csv_file_data)

    def test_cmmapi_get_users_role(self):
        """
            test data users role report.
        """
        task_input = {}
        with patch('lms.djangoapps.instructor_task.tasks_helper.runner._get_current_task'):
            result = generate(
                None, None, self.course.id,
                task_input, 'CMM-API-STUDENT-DATA'
            )
        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        header_row = ",".join(['Username', 'Email', 'Run', 'Rol'])
        staff_row = ",".join([
            self.user_instructor.username,
            self.user_instructor.email,
            '',
            'Docente/Equipo'
        ])
        student1_row = ",".join([
            self.student.username,
            self.student.email,
            '',
            'Estudiante'
        ])
        expected_data = [header_row, staff_row, student1_row]
        self._verify_csv_file_report(report_store, expected_data)

    def test_cmmapi_get_users_role_with_run(self):
        """
            test data users role report with edxloginuser model
        """
        try:
            from uchileedxlogin.models import EdxLoginUser
        except ImportError:
            self.skipTest("uchileedxlogin does not installed")

        task_input = {}
        EdxLoginUser.objects.create(user=self.user_instructor, run='022345678K')
        EdxLoginUser.objects.create(user=self.student, run='012345678K')
        with patch('lms.djangoapps.instructor_task.tasks_helper.runner._get_current_task'):
            result = generate(
                None, None, self.course.id,
                task_input, 'CMM-API-STUDENT-DATA'
            )
        report_store = ReportStore.from_config(config_name='GRADES_DOWNLOAD')
        header_row = ",".join(['Username', 'Email', 'Run', 'Rol'])
        staff_row = ",".join([
            self.user_instructor.username,
            self.user_instructor.email,
            '022345678K',
            'Docente/Equipo'
        ])
        student1_row = ",".join([
            self.student.username,
            self.student.email,
            '012345678K',
            'Estudiante'
        ])
        expected_data = [header_row, staff_row, student1_row]
        self._verify_csv_file_report(report_store, expected_data)