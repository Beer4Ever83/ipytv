#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

REPO_DIR=$(realpath "${my_dir}/..")

pushd "${REPO_DIR}" >/dev/null || abort
uv run ruff check . || abort "ruff reported linting errors"
uv run ruff format --check . || abort "ruff reported formatting errors"
popd >/dev/null || abort

exit "${TRUE}"
