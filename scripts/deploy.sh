#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

if [[ $# -gt 0 && $# -ne 1 && "$1" != '--test' ]]; then
    echo "The only supported, optional parameter is --test" >&2
    abort
fi

# TestPyPI rejects re-used filenames and PEP 440 forbids the "+g<hash>" local
# segment, so give each test build a unique, traceable version keyed on the CI
# run number: <next release>.dev<run number>. Re-running the *same* workflow
# reuses the run number and will fail on the duplicate upload — trigger a fresh
# run instead. Production releases are tagged and pass no argument, so they keep
# the exact tag version.
if [[ "$1" == '--test' ]]; then
    last_tag=$(git -C "${my_dir}/.." describe --tags --abbrev=0) \
        || abort "No git tag found to derive the version from"
    version=${last_tag#v}                                    # tolerate a "v" prefix
    next_release="${version%.*}.$(( ${version##*.} + 1 ))"   # bump the patch
    export SETUPTOOLS_SCM_PRETEND_VERSION="${next_release}.dev${GITHUB_RUN_NUMBER:-0}"
fi

# deployment in this case means packaging and publishing the library to pypi
"${my_dir}/package.sh" "$1" || abort
"${my_dir}/publish.sh" "$1" || abort

exit "${TRUE}"
