from django.contrib import admin
from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from .rest_api import CMMApiStudentProfile, CMMApiStatusTask, CMMApiORA2Report, CMMApiProblemReport, CMMApiStudentRole


urlpatterns = [
    url(r'^student-profile/$', CMMApiStudentProfile.as_view(), name='student-profile'),
    url(r'^get-all-task/$', CMMApiStatusTask.as_view(), name='get-all-task'),
    url(r'^ora2-report/$', CMMApiORA2Report.as_view(), name='ora2-report'),
    url(r'^problem-report/$', CMMApiProblemReport.as_view(), name='problem-report'),
    url(r'^users-role-report/$', CMMApiStudentRole.as_view(), name='users-role-report'),
]
