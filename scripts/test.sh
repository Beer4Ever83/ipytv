#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

LIB_DIR=$(realpath "${my_dir}/../${LIB_NAME}")
TEST_DIR=$(realpath "${my_dir}/../tests")
REPO_DIR=$(realpath "${my_dir}/..")
export PYTHONPATH=${PYTHONPATH}:${REPO_DIR}:${LIB_DIR}:${TEST_DIR}

pushd "${REPO_DIR}" >/dev/null || abort
python -m unittest discover -t "${REPO_DIR}" -s "${TEST_DIR}" -p '*_test.py'
test_result=$?
popd >/dev/null || abort

exit "$test_result"
