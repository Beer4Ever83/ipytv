#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

REPO_DIR=$(realpath "${my_dir}/..")

pushd "${REPO_DIR}" >/dev/null || abort
uv run ruff check . || abort "ruff reported linting errors"
# NOTE: `ruff format --check` is intentionally not enforced yet. It is enabled in
# the dedicated code-modernization PR, together with the one-off reformat.
popd >/dev/null || abort

exit "${TRUE}"
