#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

pushd "${my_dir}/.." >/dev/null || abort
echo "syncing the environment with uv (creating ${VIRTUALENV_DIR} and installing the dev dependency group)..."
uv sync || abort "Failure while syncing the environment with uv"
echo "done"
echo "activate the virtual env with: source ${PWD}/${VIRTUALENV_DIR}/bin/activate"
popd >/dev/null || abort

exit "$TRUE"
