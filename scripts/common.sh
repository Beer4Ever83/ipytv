# Global settings --------------------------------------------------------------
set -o pipefail

# Variables --------------------------------------------------------------------
TRUE=$(true; echo $?)
FALSE=$(false; echo $?)
VIRTUALENV_DIR=.venv
DIST_DIR=dist
LIB_NAME=ipytv
TAG_NAME=ipytv
PACKAGE_NAME=m3u-ipytv
TEST_CONTAINER_NAME=test_ipytv
LINT_CONTAINER_NAME=lint_ipytv
TEST_IN_CONTAINER=/usr/bin/runtest
LINT_IN_CONTAINER=/usr/bin/runlint
VERSION=${TRAVIS_TAG}
if [[ -n "${CIRCLE_TAG}" ]]; then
    VERSION="${CIRCLE_TAG}"
fi
TEST_VERSION="0.0.${TRAVIS_BUILD_NUMBER}"
if [[ -n "${CIRCLE_BUILD_NUM}" ]]; then
    TEST_VERSION="0.0.${CIRCLE_BUILD_NUM}"
fi

# Functions --------------------------------------------------------------------
function delete_container() {
    container_name=$1
    local container_id=$(docker ps -q -a -f name="${container_name}")
    if [[ -n "${container_id}" ]]; then
        docker rm -f "${container_id}" >/dev/null
    fi
}
