#!/bin/dash
pip install -e /openedx/requirements/cmmapi

cd /openedx/requirements/cmmapi
cp /openedx/edx-platform/setup.cfg .
mkdir test_root
cd test_root/
ln -s /openedx/staticfiles .

cd /openedx/requirements/cmmapi

#openedx-assets collect --settings=prod.assets
EDXAPP_TEST_MONGO_HOST=mongodb python -Wd -m pytest --ds=cms.envs.test --junitxml=/openedx/edx-platform/reports/cms/nosetests.xml /openedx/requirements/cmmapi/cmmapi/tests/tests_cms.py
#DJANGO_SETTINGS_MODULE=lms.envs.test EDXAPP_TEST_MONGO_HOST=mongodb pytest cmmapi/tests.py