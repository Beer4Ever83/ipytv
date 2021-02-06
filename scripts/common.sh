# Variables --------------------------------------------------------------------
TRUE=$(true; echo $?)
FALSE=$(false; echo $?)
VIRTUALENV_DIR=.venv
LIB_NAME=ipytv
TAG_NAME=ipytv
TEST_CONTAINER_NAME=test_ipytv
LINT_CONTAINER_NAME=lint_ipytv
TEST_IN_CONTAINER=/usr/bin/mytest
LINT_IN_CONTAINER=/usr/bin/mylint

# Functions --------------------------------------------------------------------
function delete_container() {
    container_name=$1
    local container_id=$(docker ps -q -a -f name="${container_name}")
    if [[ -n "${container_id}" ]]; then
        docker rm -f "${container_id}" >/dev/null
    fi
}
