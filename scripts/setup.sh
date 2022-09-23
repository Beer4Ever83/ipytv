#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

function is_virtualenv() {
    [[ -n "${VIRTUAL_ENV}" ]]
    return $?
}

function create_venv() {
    echo "creating virtual env in ${VIRTUALENV_DIR}..."
    if [[ -d "${VIRTUALENV_DIR}" ]]; then
        echo "directory ${VIRTUALENV_DIR} already existing, skipping virtual env creation."
        echo "activating existing virtual env... "
        # shellcheck source=.venv/bin/activate
        source "${PWD}/${VIRTUALENV_DIR}/bin/activate" || abort "Failure while activating the virtual environment"
        echo "done"
    else
        python -m venv "${VIRTUALENV_DIR}" || abort "Failure while creating the virtual environment"
        echo "virtual env successfully created."
    fi
    echo "Please activate this virtual env by running the following command in your shell:"
    echo "source ${PWD}/${VIRTUALENV_DIR}/bin/activate"
    echo "activating virtual env..."
    source "${VIRTUALENV_DIR}/bin/activate"
    echo "done"
}

function upgrade_pip() {
    echo "upgrading pip..."
    pip install --upgrade pip >/dev/null || abort "Failure while upgrading pip"
    echo "done"
}

function install_requirements() {
    # shellcheck source=.venv/bin/activate
    is_virtualenv || source "${PWD}/${VIRTUALENV_DIR}/bin/activate"
    local requirement_files=''
    requirement_files=$(find . -maxdepth 1 -name 'requirements*.txt')
    for reqs in $requirement_files; do
        echo "installing python dependencies from ${reqs}..."
        pip install -r "${reqs}" >/dev/null || abort "Failure while installing dependencies from ${reqs}"
        echo "done"
    done
}

pushd "${my_dir}/.." >/dev/null || abort
if is_virtualenv; then
    echo "the current shell already runs a virtual environment. Skipping creation."
else
    create_venv
fi
upgrade_pip
install_requirements
popd >/dev/null || abort

exit "$TRUE"
