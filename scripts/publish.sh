#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

REPO_DIR=$(realpath "${my_dir}/..")

pushd "${REPO_DIR}" >/dev/null || abort
if [[ $1 == '--test' ]]; then
    # TestPyPI: token-based, so it is runnable locally.
    [[ -n "${PYPI_TEST_TOKEN}" ]] || abort "PYPI_TEST_TOKEN is not set"
    uv publish \
        --publish-url https://test.pypi.org/legacy/ \
        --token "${PYPI_TEST_TOKEN}" \
        "${DIST_DIR}"/* || abort "Failure while uploading the package to TestPyPI"
else
    # Production PyPI: OIDC Trusted Publishing. Only works inside GitHub Actions
    # (with "id-token: write"); intentionally not runnable locally.
    uv publish --trusted-publishing automatic "${DIST_DIR}"/* \
        || abort "Failure while uploading the package to PyPI"
fi
popd >/dev/null || abort

exit "$TRUE"
