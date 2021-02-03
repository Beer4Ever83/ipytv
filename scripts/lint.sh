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

function exclude_convention_errors() {
    exit_code=$1
    [[ $((exit_code & CONVENTION_MASK)) -gt 0 ]] && echo $((exit_code-CONVENTION_MASK))
}

SRC_DIR=$(realpath "${my_dir}/../${APP_NAME}")
pushd "${SRC_DIR}" >/dev/null || exit "$FALSE"
pylint ./*
lint_result=$?
decode_pylint_exit_code ${lint_result}
popd >/dev/null || exit "$FALSE"
exit_code=$(exclude_convention_errors "$lint_result")
exit "${exit_code}"
