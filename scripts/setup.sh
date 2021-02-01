#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

function create_venv() {
    echo "creating virtual env in ${VIRTUALENV_DIR}..."
    if [[ -d "${VIRTUALENV_DIR}" ]]; then
        echo "directory ${VIRTUALENV_DIR} already existing, skipping virtual env creation."
        echo "activating existing virtual env... "
        source "${PWD}/${VIRTUALENV_DIR}/bin/activate" || exit "$FALSE"
        echo "done"
    else
        python3 -m venv "${VIRTUALENV_DIR}" || exit "$FALSE"
        echo "virtual env successfully created."
    fi
    echo "Please activate this virtual env by running the following command in your shell:"
    echo "source ${PWD}/${VIRTUALENV_DIR}/bin/activate"
}

function install_requirements() {
    echo "installing python dependencies from requirements.txt..."
    # shellcheck source=.venv/bin/activate
    source "${PWD}/${VIRTUALENV_DIR}/bin/activate"
    pip3 install -r ./requirements.txt >/dev/null || exit "$FALSE"
    echo "done"
}

pushd "${my_dir}/.." >/dev/null || exit "$FALSE"
if [[ -z "${VIRTUAL_ENV}" ]]; then
    create_venv
else
    echo "the current shell already runs a virtual environment. Skipping creation."
fi
install_requirements
popd >/dev/null || exit "$FALSE"

exit "$TRUE"
