#!/usr/bin/env python
# -- coding: utf-8 --

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User
from django.db import transaction
from django.views.decorators.cache import cache_control
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle
from .serializers import CMMCourseSerializer, CMMProblemSerializer
from .utils import get_students_features, get_status_tasks, utils_export_ora2_data, get_problem_responses, get_students_roles
from openedx.core.lib.api.authentication import BearerAuthentication
from datetime import datetime as dt
from rest_framework import permissions
from rest_framework import status
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
import logging

logger = logging.getLogger(__name__)

class CustomUserRateThrottle(UserRateThrottle):
    try:
        rate= settings.CMM_API_RATE
    except Exception:
        rate= '1/minute'

class CMMApiStudentProfile(APIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [CustomUserRateThrottle]

    @transaction.non_atomic_requests
    def dispatch(self, args, **kwargs):
        return super(CMMApiStudentProfile, self).dispatch(args, **kwargs)

    def post(self, request, format=None):
        if not request.user.is_anonymous:
            serializer = CMMCourseSerializer(data=request.data)
            if serializer.is_valid():
                response = get_students_features(request, serializer.data['course_id'])
                return Response(data=response, status=status.HTTP_200_OK)
            else:
                logger.error("CMMApi - StudentProfile - serializer is not valid")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error("CMMApi - StudentProfile - User is Anonymous or dont have permission")
            return Response({'error': 'User dont have permission'}, status=status.HTTP_400_BAD_REQUEST)

class CMMApiORA2Report(APIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [CustomUserRateThrottle]

    @transaction.non_atomic_requests
    def dispatch(self, args, **kwargs):
        return super(CMMApiORA2Report, self).dispatch(args, **kwargs)

    def post(self, request, format=None):
        """
        Traceback (most recent call last):
        File "/openedx/edx-platform/lms/djangoapps/instructor_task/api_helper.py", line 450, in submit_task
            task_class.apply_async(task_args, task_id=task_id)
        AttributeError: 'function' object has no attribute 'apply_async'
        """
        if not request.user.is_anonymous:
            serializer = CMMCourseSerializer(data=request.data)
            if serializer.is_valid():
                response = utils_export_ora2_data(request, serializer.data['course_id'])
                return Response(data=response, status=status.HTTP_200_OK)
            else:
                logger.error("CMMApi - ORA2 - serializer is not valid")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error("CMMApi - ORA2 - User is Anonymous or dont have permission")
            return Response({'error': 'User dont have permission'}, status=status.HTTP_400_BAD_REQUEST)

class CMMApiStatusTask(APIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [CustomUserRateThrottle]

    def get(self, request, format=None):
        if not request.user.is_anonymous:
            serializer = CMMCourseSerializer(data=request.data)
            if serializer.is_valid():
                response = get_status_tasks(serializer.data['course_id'])
                return Response(data=response, status=status.HTTP_200_OK)
            else:
                logger.error("CMMApi - StatusTask - serializer is not valid")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error("CMMApi - StatusTask - User is Anonymous or dont have permission")
            return Response({'error': 'User dont have permission'}, status=status.HTTP_400_BAD_REQUEST)

class CMMApiProblemReport(APIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [CustomUserRateThrottle]

    @transaction.non_atomic_requests
    def dispatch(self, args, **kwargs):
        return super(CMMApiProblemReport, self).dispatch(args, **kwargs)

    def post(self, request, format=None):
        if not request.user.is_anonymous:
            serializer = CMMProblemSerializer(data=request.data)
            if serializer.is_valid():
                response = get_problem_responses(request, serializer.data['block_id'])
                return Response(data=response, status=status.HTTP_200_OK)
            else:
                logger.error("CMMApi - ProblemReport - serializer is not valid")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error("CMMApi - ProblemReport - User is Anonymous or dont have permission")
            return Response({'error': 'User dont have permission'}, status=status.HTTP_400_BAD_REQUEST)

class CMMApiStudentRole(APIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [CustomUserRateThrottle]

    @transaction.non_atomic_requests
    def dispatch(self, args, **kwargs):
        return super(CMMApiStudentRole, self).dispatch(args, **kwargs)

    def post(self, request, format=None):
        if not request.user.is_anonymous:
            serializer = CMMCourseSerializer(data=request.data)
            if serializer.is_valid():
                response = get_students_roles(request, serializer.data['course_id'])
                return Response(data=response, status=status.HTTP_200_OK)
            else:
                logger.error("CMMApi - StudentRole - serializer is not valid")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error("CMMApi - StudentRole - User is Anonymous or dont have permission")
            return Response({'error': 'User dont have permission'}, status=status.HTTP_400_BAD_REQUEST)