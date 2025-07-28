# Global settings --------------------------------------------------------------
set -o pipefail

# Variables --------------------------------------------------------------------
export TRUE=$(true; echo $?)
export FALSE=$(false; echo $?)
export VIRTUALENV_DIR=.venv
export DIST_DIR=dist
export LIB_NAME=ipytv
export TAG_NAME=ipytv
export APP_NAME=m3u-ipytv
export PACKAGE_PREFIX=m3u_ipytv
export TEST_CONTAINER_NAME=test_ipytv
export LINT_CONTAINER_NAME=lint_ipytv
export TEST_IN_CONTAINER=/usr/bin/runtest
export LINT_IN_CONTAINER=/usr/bin/runlint
export VERSION="${CIRCLE_TAG}"
export TEST_VERSION="0.1.${CIRCLE_BUILD_NUM:-0}"
export MYPY_CACHE_DIR='.mypy_cache'
export PKGDATA_FILE=pkgdata.txt

# Functions --------------------------------------------------------------------
function delete_container() {
    container_name=$1
    local container_id
    container_id=$(docker ps -q -a -f name="${container_name}")
    if [[ -n "${container_id}" ]]; then
        docker rm -f "${container_id}" >/dev/null
    fi
}

function abort() {
    [[ $# -gt 0 ]] && echo "$*" >&2
    exit "${FALSE}"
}
