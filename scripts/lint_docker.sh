#!/usr/bin/env bash
set -x
my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

function delete_lint_container() {
    delete_container "${LINT_CONTAINER_NAME}"
}

trap delete_lint_container EXIT INT

pushd "${my_dir}/.." >/dev/null || exit "$FALSE"
docker run --name "${LINT_CONTAINER_NAME}" --entrypoint "${LINT_IN_CONTAINER}" "${TAG_NAME}"
lint_result=$(docker inspect "${LINT_CONTAINER_NAME}" --format='{{.State.ExitCode}}')
delete_lint_container || exit "$FALSE"
popd >/dev/null || exit "$FALSE"
exit "$lint_result"
