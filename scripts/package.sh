#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

function cleanup() {
    rm "${DIST_DIR}"/*
    find . -type d -path "./${VIRTUALENV_DIR}" -prune -false -o -name '*.egg-info' -exec rm -rf {} \;
}

function test_package() {
    # shellcheck disable=SC2155
    local TEMP_DIR=$(mktemp -dt)
    [[ -z "$TEMP_DIR" ]] && exit "$FALSE"
    python3 -m venv "${TEMP_DIR}/.testvenv" || exit "$FALSE"
    source "${TEMP_DIR}/.testvenv/bin/activate" || exit "$FALSE"
    pip3 install "${DIST_DIR}/${PACKAGE_NAME}-${PACKAGE_VERSION}.tar.gz" || exit "$FALSE"
    # shellcheck disable=SC2155
    local SHOW_OUTPUT=$(pip3 show "${PACKAGE_NAME}")
    echo "$SHOW_OUTPUT" | grep -q "Version: ${PACKAGE_VERSION}" || exit "$FALSE"
    deactivate
    rm -rf "${TEMP_DIR}"
}

REPO_DIR=$(realpath "${my_dir}/..")
export PACKAGE_VERSION=${VERSION}
if [[ $1 == '--test' ]]; then
    export PACKAGE_VERSION=${TEST_VERSION}
fi

pushd "${REPO_DIR}" >/dev/null || exit "$FALSE"
cleanup
python3 -m build --sdist || exit "$FALSE"
twine check dist/* || exit "$FALSE"
test_package
popd >/dev/null || exit "$FALSE"
exit "$TRUE"
