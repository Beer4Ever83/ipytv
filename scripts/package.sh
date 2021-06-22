#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

REPO_DIR=$(realpath "${my_dir}/..")
PACKAGE_VERSION=${TRAVIS_TAG}
if [[ $1 == '--test' ]]; then
    PACKAGE_VERSION="0.0.${TRAVIS_BUILD_NUMBER}"
fi

pushd "${REPO_DIR}" >/dev/null || exit "$FALSE"
pip show build || pip3 install build
python3 -m build --sdist
twine check dist/* || exit "$FALSE"
popd >/dev/null || exit "$FALSE"
exit "$TRUE"
