#!/usr/bin/env python
# -- coding: utf-8 --

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CMMSerializer
from .utils import default_function
from openedx.core.lib.api.authentication import BearerAuthentication
from datetime import datetime as dt
from rest_framework import permissions
from rest_framework import status
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
import logging

logger = logging.getLogger(__name__)

class CMMApi(APIView):
    authentication_classes = (BearerAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        if not request.user.is_anonymous:
            serializer = CMMSerializer(data=request.data)
            if serializer.is_valid():
                result = self.validate(serializer.data)
                if result:
                    return Response(data={'result':'success'}, status=status.HTTP_200_OK)
                else:
                    return Response(data={'result':'error'}, status=status.HTTP_200_OK)
            else:
                logger.error("CMMApi - serializer is not valid")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error("CMMApi - User is Anonymous or dont have permission")
            return Response({'error': 'User dont have permission'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        if not request.user.is_anonymous:
            serializer = CMMSerializer(data=request.data)
            if serializer.is_valid():
                result = self.validate(serializer.data)
                if result:
                    return Response(data={'result':'success'}, status=status.HTTP_200_OK)
                else:
                    return Response(data={'result':'error'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                logger.error("CMMApi - serializer is not valid")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error("CMMApi - User is Anonymous or dont have permission")
            return Response({'error': 'User dont have permission'}, status=status.HTTP_400_BAD_REQUEST)

    def validate(self, data):
        return default_function(data)