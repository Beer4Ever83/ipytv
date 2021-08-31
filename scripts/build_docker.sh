#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

pushd "${my_dir}/.." >/dev/null || abort
if [[ -n "${DOCKER_PASSWORD}" && -n "${DOCKER_USERNAME}" ]]; then
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin https://registry.hub.docker.com || abort
fi
docker build --tag "${TAG_NAME}" . || abort
popd >/dev/null || abort

exit "$TRUE"
