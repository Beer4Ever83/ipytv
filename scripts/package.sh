#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

function cleanup() {
    local egg_info_dirs=''
    egg_info_dirs=$(
        find . -type d \
        \( -path "./${VIRTUALENV_DIR}" -o -path "./${MYPY_CACHE_DIR}" -o -path ./.git -o -path ./.idea \) \
        -prune -false -o -name '*.egg-info'
    )
    local dirs_to_cleanup="${DIST_DIR:?} ${MYPY_CACHE_DIR:?} ${egg_info_dirs}"
    for dir in ${dirs_to_cleanup}; do
        [[ -d "${dir}" ]] && rm -rf "${dir}"
    done
}

function test_package() {
    # shellcheck disable=SC2155
    local TEMP_DIR=$(mktemp -dt)
    [[ -z "$TEMP_DIR" ]] && abort "Failure while creating a temporary directory (${TEMP_DIR})"
    python3 -m venv "${TEMP_DIR}/.testvenv" || abort "Failure while creating virtual environment (.testvenv)"
    source "${TEMP_DIR}/.testvenv/bin/activate" || abort "Failure while activating the test virtual environment"
    pip3 install --upgrade pip || abort "Failure while upgrading pip"
    pip3 install -r requirements-deploy.txt || abort "Failure while installing deploy requirements"
    pip3 install "${DIST_DIR}/${PACKAGE_NAME}-${PACKAGE_VERSION}.tar.gz" || abort "Failure while installing the package"
    # shellcheck disable=SC2155
    local SHOW_OUTPUT=$(pip3 show "${PACKAGE_NAME}")
    echo "$SHOW_OUTPUT" | grep -q "Version: ${PACKAGE_VERSION}" || abort "Package is not installed"
    deactivate
    rm -rf "${TEMP_DIR}"
}

REPO_DIR=$(realpath "${my_dir}/..")
export PACKAGE_VERSION=${VERSION}
if [[ $1 == '--test' ]]; then
    export PACKAGE_VERSION=${TEST_VERSION}
fi
if [[ -z "${PACKAGE_NAME}" || -z "${PACKAGE_VERSION}" ]]; then
    abort "Missing one or more mandatory variables"
fi
pushd "${REPO_DIR}" >/dev/null || abort
cleanup
python3 -m build --sdist || abort "Failure while building the package"
twine check dist/* || abort "twine reported an error"
test_package
popd >/dev/null || abort

exit "$TRUE"
