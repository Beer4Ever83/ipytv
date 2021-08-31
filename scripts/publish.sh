#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

TWINE_REPO=''
export TWINE_USERNAME="${PYPI_USERNAME}"
export TWINE_PASSWORD="${PYPI_TOKEN}"
if [[ $1 == '--test' ]]; then
    export TWINE_USERNAME="${PYPI_TEST_USERNAME}"
    export TWINE_PASSWORD="${PYPI_TEST_TOKEN}"
    TWINE_REPO='--repository testpypi'
fi

REPO_DIR=$(realpath "${my_dir}/..")

pushd "${REPO_DIR}" >/dev/null || abort
twine upload ${TWINE_REPO} "${DIST_DIR}"/* || abort "Failure while uploading the package"
popd >/dev/null || abort

exit "$TRUE"
