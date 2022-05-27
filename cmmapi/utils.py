#!/usr/bin/env python
# -- coding: utf-8 --

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import ugettext as _
from django.db import transaction
from django.urls import reverse
from urllib.parse import urlencode
from itertools import cycle
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError
from lms.djangoapps.instructor_analytics import basic as instructor_analytics_basic
from lms.djangoapps.courseware.courses import get_course_by_id, get_course_with_access
from lms.djangoapps.instructor_task.api_helper import submit_task
from lms.djangoapps.instructor_task.models import InstructorTask, ReportStore
from lms.djangoapps.instructor_task.tasks import calculate_students_features_csv, export_ora2_data, calculate_problem_responses_csv
from lms.djangoapps.instructor_task import api as task_api
from lms.djangoapps.instructor.views.instructor_task_helpers import extract_task_features
from lms.djangoapps.instructor_task.api_helper import AlreadyRunningError
from xmodule.modulestore.django import modulestore
from common.djangoapps.student import auth
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from common.djangoapps.course_action_state.models import CourseRerunState
from xmodule.modulestore import EdxJSONEncoder
from xmodule.course_module import DEFAULT_START_DATE, CourseFields
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.djangoapps.course_groups.cohorts import is_course_cohorted
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from lms.djangoapps.courseware.access import has_access
from datetime import datetime as dt
import unidecode
import logging
import json
import six
import csv
import re
import io

logger = logging.getLogger(__name__)
TASK_TYPES = ['cmmapi_profile_info_csv', 'cmmapi_problem_responses_csv', 'cmmapi_export_ora2_data']
SUCCESS_MESSAGE_TEMPLATE = _(u"The {report_type} report is being created. "
                             "To view the status of the report, see Pending Tasks below.")

def validate_course(id_curso):
    """
        Verify if course.id exists
    """
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    try:
        aux = CourseKey.from_string(id_curso)
        return CourseOverview.objects.filter(id=aux).exists()
    except InvalidKeyError:
        logger.error("CMM-Api error validate course, invalid format: {}".format(id_curso))
        return False

def validate_block(block_id):
    try:
        aux = UsageKey.from_string(block_id)
        return True
    except InvalidKeyError:
        logger.error("CMM-Api error validate block id, invalid format: {}".format(block_id))
        return False

def get_students_features(request, course_id):
    """
    Respond a summary of all enrolled students profile information.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key)
    report_type = _('enrolled learner profile')
    available_features = instructor_analytics_basic.AVAILABLE_FEATURES

    query_features = list(configuration_helpers.get_value('student_profile_download_fields', []))

    if not query_features:
        query_features = [
            'id', 'username', 'name', 'email', 'language', 'location',
            'year_of_birth', 'gender', 'level_of_education', 'mailing_address',
            'goals', 'enrollment_mode', 'verification_status',
            'last_login', 'date_joined',
        ]

    query_features_names = {
        'id': _('User ID'),
        'username': _('Username'),
        'name': _('Name'),
        'email': _('Email'),
        'language': _('Language'),
        'location': _('Location'),
        'year_of_birth': _('Birth Year'),
        'gender': _('Gender'),
        'level_of_education': _('Level of Education'),
        'mailing_address': _('Mailing Address'),
        'goals': _('Goals'),
        'enrollment_mode': _('Enrollment Mode'),
        'verification_status': _('Verification Status'),
        'last_login': _('Last Login'),
        'date_joined': _('Date Joined'),
    }

    if is_course_cohorted(course.id):
        # Translators: 'Cohort' refers to a group of students within a course.
        query_features.append('cohort')
        query_features_names['cohort'] = _('Cohort')

    if course.teams_enabled:
        query_features.append('team')
        query_features_names['team'] = _('Team')

    # For compatibility reasons, city and country should always appear last.
    query_features.append('city')
    query_features_names['city'] = _('City')
    query_features.append('country')
    query_features_names['country'] = _('Country')

    try:
        submit_calculate_students_features_csv(request, course_key, query_features)
        success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)
        return {"status": success_status}
    except AlreadyRunningError:
        return {"status": 'Already Running Task'}

def submit_calculate_students_features_csv(request, course_key, features):
    """
    Submits a task to generate a CSV containing student profile info.

    Raises AlreadyRunningError if said CSV is already being updated.
    """
    task_type = 'cmmapi_profile_info_csv'
    task_class = calculate_students_features_csv
    task_input = features
    task_key = "CMM-API-STUDENT-PROFILE-{}".format(str(course_key))

    return submit_task(request, task_type, task_class, course_key, task_input, task_key)

def get_status_tasks(course_id):
    course_key = CourseKey.from_string(course_id)
    list_task = list(InstructorTask.objects.filter(task_type__in=TASK_TYPES, course_id=course_key).values('task_type', 'task_id', 'task_state'))
    tasks = task_api.get_running_instructor_tasks(course_id)

    response_payload = {
        'tasks_url': list(map(extract_task_features, tasks)),
        'list_task':list_task
    }
    return response_payload

def export_ora2_data(request, course_id):
    """
    Pushes a Celery task which will aggregate ora2 responses for a course into a .csv
    """
    course_key = CourseKey.from_string(course_id)
    report_type = _('ORA data')
    
    try:
        submit_export_ora2_data(request, course_key)
        success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)
        return {"status": success_status}
    except AlreadyRunningError:
        return {"status": 'Already Running Task'}

def submit_export_ora2_data(request, course_key):
    """
    AlreadyRunningError is raised if an ora2 report is already being generated.
    """
    task_type = 'cmmapi_export_ora2_data'
    task_class = export_ora2_data
    task_input = {}
    task_key = "CMM-API-ORA2-REPORT-{}".format(str(course_key))

    return submit_task(request, task_type, task_class, course_key, task_input, task_key)

def get_problem_responses(request, block_id):
    """
    Initiate generation of a CSV file containing all student answers
    to a given problem.

    **Example requests**

        POST /courses/{course_id}/instructor/api/get_problem_responses {
            "problem_location": "{usage_key1},{usage_key2},{usage_key3}""
        }
        POST /courses/{course_id}/instructor/api/get_problem_responses {
            "problem_location": "{usage_key}",
            "problem_types_filter": "problem"
        }

        **POST Parameters**

        A POST request can include the following parameters:

        * problem_location: A comma-separated list of usage keys for the blocks
          to include in the report. If the location is a block that contains
          other blocks, (such as the course, section, subsection, or unit blocks)
          then all blocks under that block will be included in the report.
        * problem_types_filter: Optional. A comma-separated list of block types
          to include in the repot. If set, only blocks of the specified types will
          be included in the report.

        To get data on all the poll and survey blocks in a course, you could
        POST the usage key of the course for `problem_location`, and
        "poll, survey" as the value for `problem_types_filter`.


    **Example Response:**
    If initiation is successful (or generation task is already running):
    ```json
    {
        "status": "The problem responses report is being created. ...",
        "task_id": "4e49522f-31d9-431a-9cff-dd2a2bf4c85a"
    }
    ```

    Responds with BadRequest if any of the provided problem locations are faulty.
    """
    report_type = _('problem responses')

    try:
        submit_calculate_problem_responses_csv(request, block_id)
        success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)
        return {"status": success_status}
    except AlreadyRunningError:
        return {"status": 'Already Running Task'}

def submit_calculate_problem_responses_csv(request, problem_location):
    """
    Submits a task to generate a CSV file containing all student
    answers to a given problem.

    Raises AlreadyRunningError if said file is already being updated.
    """
    usage_key = UsageKey.from_string(problem_location)
    task_type = 'cmmapi_problem_responses_csv'
    task_class = calculate_problem_responses_csv
    task_input = {
        'problem_locations': problem_location,
        'problem_types_filter': None,
        'user_id': request.user.pk,
    }
    task_key = "CMM-API-PROBLEM-REPORT-{}".format(str(usage_key.course_key))

    return submit_task(request, task_type, task_class, usage_key.course_key, task_input, task_key)