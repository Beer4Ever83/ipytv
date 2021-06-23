#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

function cleanup() {
    rm "${DIST_DIR}"/*
    find . -type d -path "./${VIRTUALENV_DIR}" -prune -false -o -name '*.egg-info' -exec rm -rf {} \;
}

REPO_DIR=$(realpath "${my_dir}/..")
LIB_DIR=$(realpath "${my_dir}/../${LIB_NAME}")
PACKAGE_VERSION=${TRAVIS_TAG}
if [[ $1 == '--test' ]]; then
    PACKAGE_VERSION="0.0.${TRAVIS_BUILD_NUMBER}"
fi

pushd "${REPO_DIR}" >/dev/null || exit "$FALSE"
pip show build || pip3 install build || exit "$FALSE"
cleanup
python3 -m build --sdist || exit "$FALSE"
twine check dist/* || exit "$FALSE"
popd >/dev/null || exit "$FALSE"
exit "$TRUE"
