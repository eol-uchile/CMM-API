# CMM API
![https://github.com/eol-uchile/cmm-api/actions](https://github.com/eol-uchile/cmm-api/workflows/Python%20application/badge.svg)

# Install App

    docker-compose exec lms pip install -e /openedx/requirements/cmmapi
    docker-compose exec lms_worker pip install -e /openedx/requirements/cmmapi
    docker-compose exec cms pip install -e /openedx/requirements/cmmapi
    docker-compose exec cms_worker pip install -e /openedx/requirements/cmmapi

## TESTS
**Prepare tests:**

    > cd .github/
    > docker-compose run cms /openedx/requirements/cmmapi/.github/test_cms.sh
    > docker-compose run lms /openedx/requirements/cmmapi/.github/test_lms.sh
