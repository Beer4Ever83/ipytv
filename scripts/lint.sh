#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

# Run pylint
"${my_dir}"/pylint.sh || abort "pylint.sh returned errors"

# Run mypy
"${my_dir}"/mypy.sh || abort "mypy.sh returned errors"

exit "${TRUE}"
