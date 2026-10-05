#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

REPO_DIR=$(realpath "${my_dir}/..")
BENCHMARK="${REPO_DIR}/benchmarks/loadl.py"
# The report contains non-ASCII characters, which Windows consoles can't print by default.
export PYTHONUTF8=1

function usage() {
    echo "Usage: $(basename "${0}") [--base GIT_REF | --pypi VERSION]" >&2
    echo "Compares the loadl speed of the working tree with GIT_REF (default: origin/main) or a PyPI release." >&2
}

# uv is a native Windows program: give it Windows paths when running under Git Bash.
function native_path() {
    if command -v cygpath >/dev/null; then
        cygpath -m "$1"
    else
        echo "$1"
    fi
}

function cleanup() {
    [[ -d "${WORK_DIR}/base" ]] && git -C "${REPO_DIR}" worktree remove --force "${WORK_DIR}/base"
    rm -rf "${WORK_DIR}"
}

function run_benchmark() {
    local output=$1
    shift
    uv run -q --isolated --no-project "$@" python "$(native_path "${BENCHMARK}")" run "$(native_path "${output}")" \
        || abort "The benchmark run failed"
}

base_ref="origin/main"
pypi_version=""
while [[ $# -gt 0 ]]; do
    [[ $# -ge 2 ]] || { usage; abort; }
    case "$1" in
        --base) base_ref="$2" ;;
        --pypi) pypi_version="$2" ;;
        *) usage; abort ;;
    esac
    shift 2
done

WORK_DIR=$(mktemp -d) || abort "Failure while creating a temporary directory"
trap cleanup EXIT

if [[ -n "${pypi_version}" ]]; then
    base_label="${pypi_version}"
    base_with=(--with "${APP_NAME}==${pypi_version}")
else
    base_label="${base_ref} ($(git -C "${REPO_DIR}" rev-parse --short "${base_ref}"))"
    git -C "${REPO_DIR}" worktree add -q --detach "${WORK_DIR}/base" "${base_ref}" || abort "Cannot check out ${base_ref}"
    base_with=(--with-editable "$(native_path "${WORK_DIR}/base")")
fi
head_with=(--with-editable "$(native_path "${REPO_DIR}")")
head_label="current ($(git -C "${REPO_DIR}" rev-parse --short HEAD))"
[[ -n "$(git -C "${REPO_DIR}" status --porcelain)" ]] && head_label="${head_label} + local changes"

# Alternating rounds, so that a machine getting faster or slower over time affects both sides equally.
run_benchmark "${WORK_DIR}/base1.json" "${base_with[@]}"
run_benchmark "${WORK_DIR}/head1.json" "${head_with[@]}"
run_benchmark "${WORK_DIR}/head2.json" "${head_with[@]}"
run_benchmark "${WORK_DIR}/base2.json" "${base_with[@]}"

report=$(uv run -q --isolated --no-project python "$(native_path "${BENCHMARK}")" report "${base_label}" "${head_label}" \
    --base "$(native_path "${WORK_DIR}/base1.json")" "$(native_path "${WORK_DIR}/base2.json")" \
    --head "$(native_path "${WORK_DIR}/head1.json")" "$(native_path "${WORK_DIR}/head2.json")") \
    || abort "The benchmark report failed"
echo "${report}"
if [[ -n "${GITHUB_STEP_SUMMARY}" ]]; then
    echo "${report}" >>"${GITHUB_STEP_SUMMARY}"
fi

exit "${TRUE}"
