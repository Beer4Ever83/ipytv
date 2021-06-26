#!/usr/bin/env bash

my_dir=$(dirname "$(readlink -f "${0}")")
# shellcheck source=scripts/common.sh
source "${my_dir}/common.sh"

pushd "${my_dir}/.." >/dev/null || exit "$FALSE"
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin https://registry.hub.docker.com || exit "$FALSE"
docker build --tag "${TAG_NAME}" . || exit "$FALSE"
popd >/dev/null || exit "$FALSE"
exit "$TRUE"
