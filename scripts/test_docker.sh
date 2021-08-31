#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

function delete_test_container() {
    delete_container "${TEST_CONTAINER_NAME}"
}

trap delete_test_container EXIT INT

pushd "${my_dir}/.." >/dev/null || abort
docker run --name "${TEST_CONTAINER_NAME}" --entrypoint "${TEST_IN_CONTAINER}" "${TAG_NAME}"
test_result=$(docker inspect "${TEST_CONTAINER_NAME}" --format='{{.State.ExitCode}}')
delete_test_container || abort
popd >/dev/null || abort

exit "${test_result:-1}"
