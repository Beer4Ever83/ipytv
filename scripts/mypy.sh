#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

LIB_DIR=$(realpath "${my_dir}/../${LIB_NAME}")
pushd "${LIB_DIR}" >/dev/null || abort
mypy --install-types --non-interactive .
result=$?
popd >/dev/null || abort

exit "${result}"
