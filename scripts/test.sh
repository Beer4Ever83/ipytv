#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

REPO_DIR=$(realpath "${my_dir}/..")

pushd "${REPO_DIR}" >/dev/null || abort
rm -f .coverage .coverage.*
uv run coverage run -m pytest
test_result=$?
uv run coverage combine -q && uv run coverage report
if [[ -n "${GITHUB_STEP_SUMMARY}" ]]; then
    { echo "## Coverage"; echo; uv run coverage report --format=markdown; } >>"${GITHUB_STEP_SUMMARY}"
fi
popd >/dev/null || abort

exit "$test_result"
