#!/usr/bin/env python
# -- coding: utf-8 --

from django.conf import settings
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey, UsageKey
from celery import current_task, task
from common.djangoapps.student.models import CourseAccessRole
from common.djangoapps.util.file import course_filename_prefix_generator
from lms.djangoapps.instructor_task.models import InstructorTask, ReportStore
from lms.djangoapps.instructor_task.api_helper import submit_task
from lms.djangoapps.instructor_task.tasks_base import BaseInstructorTask
from lms.djangoapps.instructor_task.tasks_helper.runner import run_main_task, TaskProgress
from django.core.exceptions import FieldError
from django.utils.translation import ugettext_noop
from django.core.files.base import ContentFile
from functools import partial
from datetime import datetime as dt
from time import time
from pytz import UTC
import unidecode
import logging
import codecs
import json
import six
import csv
import io

logger = logging.getLogger(__name__)

def get_user_roles(course_key):
    """
        Get all user with role in the course
    """
    try:
        user_roles_model = list(CourseAccessRole.objects.filter(course_id=course_key).values('user__username', 'user__email','user__edxloginuser__run').distinct())
    except FieldError:
        logger.error("CMMApi - Error with UchileEdxLogin model")
        user_roles_model = list(CourseAccessRole.objects.filter(course_id=course_key).values('user__username', 'user__email').distinct())
    return user_roles_model

def get_user_info_role(course_key):
    user_roles_model = get_user_roles(course_key)
    usernames_roles = [x['user__username'] for x in user_roles_model]
    # try to get rut from edxloginuser model if this dont exists only get id, username and email
    try:
        enrolled_students = User.objects.filter(courseenrollment__course_id=course_key,courseenrollment__is_active=1).order_by('username').values('username', 'email', 'edxloginuser__run')
        instructor_users = [[x['user__username'],x['user__email'],x['user__edxloginuser__run'] or '', 'Docente/Equipo'] for x in user_roles_model]
        students_users = [[x['username'],x['email'],x['edxloginuser__run'] or '', 'Estudiante'] for x in enrolled_students if x['username'] not in usernames_roles]
        return instructor_users + students_users
    except FieldError:
        logger.error("CMMApi - Error with UchileEdxLogin model")
        enrolled_students = User.objects.filter(courseenrollment__course_id=course_key,courseenrollment__is_active=1).order_by('username').values('username', 'email')
        instructor_users = [[x['user__username'],x['user__email'],'', 'Docente/Equipo'] for x in user_roles_model]
        students_users = [[x['username'],x['email'],'', 'Estudiante'] for x in enrolled_students if x['username'] not in usernames_roles]
        return instructor_users + students_users

def task_process_data(request, course_key):
    task_type = 'cmmapi_student_data'
    task_class = process_data
    task_input = {}
    task_key = "CMM-API-STUDENT-DATA-{}".format(str(course_key))

    return submit_task(
        request,
        task_type,
        task_class,
        course_key,
        task_input,
        task_key)

@task(base=BaseInstructorTask, queue='edx.lms.core.low')
def process_data(entry_id, xmodule_instance_args):
    action_name = ugettext_noop('generated')
    task_fn = partial(generate, xmodule_instance_args)

    return run_main_task(entry_id, task_fn, action_name)

def generate(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing
    all user and role, and store using a `ReportStore`.
    """
    start_time = time()
    start_date = dt.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'CMMAPI Student Role - Calculating students data'}
    task_progress.update_task_state(extra_meta=current_step)
    
    data = get_user_info_role(course_id)
    report_store = ReportStore.from_config('GRADES_DOWNLOAD')
    csv_name = 'Reporte_Roles'

    report_name = u"{course_prefix}_{csv_name}_{timestamp_str}.csv".format(
        course_prefix=course_filename_prefix_generator(course_id),
        csv_name=csv_name,
        timestamp_str=start_date.strftime("%Y-%m-%d-%H%M")
    )
    output_buffer = ContentFile('')
    if six.PY2:
        output_buffer.write(codecs.BOM_UTF8)
    csvwriter = csv.writer(output_buffer)
    header = ['Username', 'Email','Run', 'Rol']
    csvwriter.writerow(header)
    csvwriter.writerows(ReportStore()._get_utf8_encoded_rows(data))

    current_step = {'step': 'CMMAPI Student Role - Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    output_buffer.seek(0)
    report_store.store(course_id, report_name, output_buffer)
    current_step = {
        'step': 'CMMAPI Student Role - CSV uploaded',
        'report_name': report_name,
    }
    return task_progress.update_task_state(extra_meta=current_step)

