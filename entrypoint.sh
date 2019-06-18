#!/usr/bin/env bash

set -e
set -o pipefail

exec "$@" \
    --interval=${CHECK_INTERVAL:-60} \
    --namespace=${NAMESPACE} \
    --seconds-between-restarts=${DEFAULT_SECONDS_BETWEEN_RESTARTS:-20} \
    --frame-size-in-seconds=${DEFAULT_FRAME_SIZE:-300} \
    --max-restarts-in-frame=${DEFAULT_FRAME_SIZE:-5} \
    --seconds-between-next-frame=${DEFAULT_SECONDS_BETWEEN_NEXT_FRAME:-1500} \
    --max-checks-to-give-up=${DEFAULT_MAX_CHECKS_TO_GIVE_UP:-30} \
    --max-historic-entries=${DEFAULT_MAX_HISTORIC_ENTRIES:-20} \
    --enable-cleaning-duplicated-services=${DEFAULT_ENABLE_DUPLICATED_SERVICES_REMOVING:-FALSE} \
    --docker-socket=${DOCKER_SOCK:-/var/run/docker.sock}

