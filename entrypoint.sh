#!/usr/bin/env bash

set -e
set -o pipefail

# set proper timezone
echo "${TZ}" > /etc/timezone

BOOLEAN_ARGS=""

if [[ ${ENABLE_CLEANING_DUPLICATED_SERVICES} == "true" ]]; then
    BOOLEAN_ARGS="${BOOLEAN_ARGS} --enable-cleaning-duplicated-services"
fi

exec "$@" \
    --interval=${CHECK_INTERVAL} \
    --namespace=${NAMESPACE} \
    --seconds-between-restarts=${DEFAULT_SECONDS_BETWEEN_RESTARTS} \
    --frame-size-in-seconds=${DEFAULT_FRAME_SIZE} \
    --max-restarts-in-frame=${DEFAULT_MAX_RESTARTS_IN_FRAME} \
    --seconds-between-next-frame=${DEFAULT_SECONDS_BETWEEN_NEXT_FRAME} \
    --max-checks-to-give-up=${DEFAULT_MAX_CHECKS_TO_GIVE_UP} \
    --max-historic-entries=${DEFAULT_MAX_HISTORIC_ENTRIES} \
    --http-address=${HTTP_ADDRESS} \
    --http-port=${HTTP_PORT} \
    --http-prefix=${HTTP_PREFIX} \
    --notify-url=${DEFAULT_NOTIFY_URL} \
    --notify-level=${DEFAULT_NOTIFY_LEVEL} \
    ${BOOLEAN_ARGS}
    # --docker-socket=${DOCKER_SOCK:-/var/run/docker.sock}
