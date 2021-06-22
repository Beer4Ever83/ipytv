#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"
TWINE_REPO=''
if [[ $1 == '--test' ]]; then
    TWINE_REPO='--repository testpypi'
fi

REPO_DIR=$(realpath "${my_dir}/..")

pushd "${REPO_DIR}" >/dev/null || exit "$FALSE"
twine upload ${TWINE_REPO} dist/*
popd >/dev/null || exit "$FALSE"
exit "$TRUE"
