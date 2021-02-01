#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

SRC_DIR=$(realpath "${my_dir}/../${APP_NAME}")
APP_DIR="$SRC_DIR/app"
export PYTHONPATH=${PYTHONPATH}:${SRC_DIR}

pushd "${SRC_DIR}" >/dev/null || exit "$FALSE"
python3 "${APP_DIR}/${APP_ENTRYPOINT}" "$@"
exit_code=$?
popd >/dev/null || exit "$FALSE"
exit "$exit_code"
