#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

function delete_app_container() {
    delete_container "${APP_CONTAINER_NAME}"
}

trap delete_app_container EXIT INT

docker run -it --name "${APP_CONTAINER_NAME}" "${TAG_NAME}" "$@" || exit "$FALSE"
exit_code=$(docker inspect "${APP_CONTAINER_NAME}" --format='{{.State.ExitCode}}')
delete_app_container || exit "$FALSE"
exit "$exit_code"
