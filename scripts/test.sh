#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

SRC_DIR=$(realpath "${my_dir}/../${APP_NAME}")
TEST_DIR=$SRC_DIR/test
export PYTHONPATH=${PYTHONPATH}:${SRC_DIR}

pushd "${SRC_DIR}" >/dev/null || exit "$FALSE"
python3 -m unittest discover -s "${TEST_DIR}" -p '*_test.py'
test_result=$?
popd >/dev/null || exit "$FALSE"
exit "$test_result"
