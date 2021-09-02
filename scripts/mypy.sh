#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

REPO_DIR=$(realpath "${my_dir}/..")
LIB_DIR=$(realpath "${REPO_DIR}/${LIB_NAME}")
CACHE_DIR="${REPO_DIR}/${MYPY_CACHE_DIR}"
pushd "${LIB_DIR}" >/dev/null || abort
mypy --install-types --non-interactive --cache-dir="${CACHE_DIR}" .
result=$?
popd >/dev/null || abort

exit "${result}"
