# CMM API
![https://github.com/eol-uchile/cmm-api/actions](https://github.com/eol-uchile/cmm-api/workflows/Python%20application/badge.svg)

# Install App

    docker-compose exec lms pip install -e /openedx/requirements/cmmapi
    docker-compose exec lms_worker pip install -e /openedx/requirements/cmmapi

# Configuration

Set rate limit in lms.yml

    CMM_API_RATE: '1/minute'

## TESTS
**Prepare tests:**

    > cd .github/
    > docker-compose run lms /openedx/requirements/cmmapi/.github/test_lms.sh
