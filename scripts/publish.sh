#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

# Publishing is allowed ONLY from GitHub Actions, via OIDC Trusted Publishing.
# Local pushes to PyPI and TestPyPI are intentionally forbidden: there are no
# tokens to leak, and releases are reproducible from CI alone.
[[ "${GITHUB_ACTIONS}" == "true" ]] \
    || abort "Publishing is only allowed from GitHub Actions (OIDC Trusted Publishing)"

REPO_DIR=$(realpath "${my_dir}/..")

pushd "${REPO_DIR}" >/dev/null || abort
if [[ $1 == '--test' ]]; then
    uv publish \
        --trusted-publishing always \
        --publish-url https://test.pypi.org/legacy/ \
        "${DIST_DIR}"/* || abort "Failure while uploading the package to TestPyPI"
else
    uv publish --trusted-publishing always "${DIST_DIR}"/* \
        || abort "Failure while uploading the package to PyPI"
fi
popd >/dev/null || abort

exit "$TRUE"
