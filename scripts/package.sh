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

function installation_test() {
    # shellcheck disable=SC2155
    local TEMP_DIR=$(mktemp -dt)
    [[ -z "$TEMP_DIR" ]] && abort "Failure while creating a temporary directory (${TEMP_DIR})"
    python -m venv "${TEMP_DIR}/.testvenv" || abort "Failure while creating virtual environment (.testvenv)"
    source "${TEMP_DIR}/.testvenv/bin/activate" || abort "Failure while activating the test virtual environment"
    pip install --upgrade pip || abort "Failure while upgrading pip"
    # The version is derived from git tags at build time, so locate the wheel by
    # pattern (via find, not ls) rather than constructing an exact filename.
    local WHEEL
    WHEEL=$(find "${DIST_DIR}" -maxdepth 1 -type f -name "${PACKAGE_PREFIX}-*.whl" | head -n 1)
    [[ -n "${WHEEL}" && -r "${WHEEL}" ]] || abort "No wheel found in ${DIST_DIR}"
    pip install "${WHEEL}" || abort "Failure while installing the package"
    # Derive the expected version from the wheel filename
    # (m3u_ipytv-<version>-py3-none-any.whl) and assert pip installed exactly it.
    local WHEEL_FILE=${WHEEL##*/}
    local EXPECTED_VERSION=${WHEEL_FILE#"${PACKAGE_PREFIX}"-}
    EXPECTED_VERSION=${EXPECTED_VERSION%%-*}
    # Capture first, then match: piping pip directly into "grep -q" trips
    # "set -o pipefail" because grep closes the pipe early (SIGPIPE on pip).
    local SHOW_OUTPUT
    SHOW_OUTPUT=$(pip show "${APP_NAME}")
    [[ "${SHOW_OUTPUT}" == *"Version: ${EXPECTED_VERSION}"* ]] \
        || abort "Expected version ${EXPECTED_VERSION} is not the installed one"
    # Verify that the command-line tools were actually deployed, with read and
    # execute permissions, at their expected install location. This catches a
    # missing/misnamed entry point even though "pip show" above still succeeds.
    local BIN_DIR="${VIRTUAL_ENV}/bin"
    [[ -r "${BIN_DIR}/iptv2json" && -x "${BIN_DIR}/iptv2json" ]] || abort "The iptv2json CLI was not deployed correctly"
    [[ -r "${BIN_DIR}/json2iptv" && -x "${BIN_DIR}/json2iptv" ]] || abort "The json2iptv CLI was not deployed correctly"
    deactivate
    rm -rf "${TEMP_DIR}"
}

REPO_DIR=$(realpath "${my_dir}/..")
pushd "${REPO_DIR}" >/dev/null || abort
cleanup
uv build || abort "Failure while building the package"
uvx twine check "${DIST_DIR}"/* || abort "twine reported an error"
installation_test
popd >/dev/null || abort

exit "$TRUE"
