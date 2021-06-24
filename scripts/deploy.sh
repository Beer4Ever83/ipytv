#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

if [[ $# -gt 0 && $# -ne 1 && "$1" != '--test' ]]; then
    echo "The only supported, optional parameter is --test" >&2
    exit "$FALSE"
fi

# deployment in this case means packaging and publishing the library to pypi
"${my_dir}/package.sh" "$1" || exit "$FALSE"
"${my_dir}/publish.sh" "$1" || exit "$FALSE"
