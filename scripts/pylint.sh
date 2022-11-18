#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

# pylint exit code masks
#  0: no error
NO_ERROR=0
#  1: fatal message issued
FATAL_MASK=1
#  2: error message issued
ERROR_MASK=2
#  4: warning message issued
WARNING_MASK=4
#  8: refactor message issued
REFACTOR_MASK=8
# 16: convention message issued
CONVENTION_MASK=16
# 32: usage error
USAGE_ERROR_MASK=32

function decode_pylint_exit_code() {
    exit_code=$1
    [[ ${exit_code} -eq ${NO_ERROR} ]] && echo "pylint: no error"
    [[ $((exit_code & FATAL_MASK)) -gt 0 ]] && echo "pylint: fatal message issued"
    [[ $((exit_code & ERROR_MASK)) -gt 0 ]] && echo "pylint: error message issued"
    [[ $((exit_code & WARNING_MASK)) -gt 0 ]] && echo "pylint: warning message issued"
    [[ $((exit_code & REFACTOR_MASK)) -gt 0 ]] && echo "pylint: refactor message issued"
    [[ $((exit_code & CONVENTION_MASK)) -gt 0 ]] && echo "pylint: convention message issued"
    [[ $((exit_code & USAGE_ERROR_MASK)) -gt 0 ]] && echo "pylint: usage error"
}

function exclude_from_return_code() {
    exclude_mask=$1
    exit_code=$2
    [[ $((exit_code & exclude_mask)) -gt 0 ]] && echo $((exit_code-exclude_mask))
}

LIB_DIR=$(realpath "${my_dir}/../${LIB_NAME}")
pushd "${LIB_DIR}" >/dev/null || abort
pylint --max-line-length=120 ./*
lint_result=$?
decode_pylint_exit_code ${lint_result}
popd >/dev/null || abort
exit_code=${lint_result}
EXCLUSION_LIST="${REFACTOR_MASK} ${CONVENTION_MASK}"
for result_to_exclude in ${EXCLUSION_LIST}; do
    exit_code=$(exclude_from_return_code "${result_to_exclude}" "${exit_code}")
done

exit "${exit_code}"
