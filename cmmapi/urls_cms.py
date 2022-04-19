from django.contrib import admin
from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from .rest_api import CMMApi


urlpatterns = [
    url(r'^test-cms/$', CMMApi.as_view(), name='test-cms'),
]
