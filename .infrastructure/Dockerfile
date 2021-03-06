FROM multiarch/alpine:x86_64-v3.9

ARG arch=x86_64

ENV CHECK_INTERVAL=90 \
    NAMESPACE= \
    DEFAULT_SECONDS_BETWEEN_RESTARTS=15 \
    DEFAULT_FRAME_SIZE=300 \
    DEFAULT_MAX_RESTARTS_IN_FRAME=2 \
    DEFAULT_SECONDS_BETWEEN_NEXT_FRAME=600 \
    DEFAULT_MAX_CHECKS_TO_GIVE_UP=50 \
    DEFAULT_MAX_HISTORIC_ENTRIES=50 \
    DEFAULT_ENABLE_DUPLICATED_SERVICES_REMOVING=true \
    DEFAULT_ENABLE_AUTO_HEAL=true \
    TZ=Europe/Warsaw \
    HTTP_ADDRESS=0.0.0.0 \
    HTTP_PORT=80 \
    HTTP_PREFIX= \
    DEFAULT_NOTIFY_URL= \
    DEFAULT_NOTIFY_LEVEL=info \
    DB_PATH=/var/database.sqlite3

COPY ./ /opt/repairman

RUN apk add --no-cache curl python3 bash git make tzdata \
    && cd /opt/repairman \
    && python3 -m pip install -r /opt/repairman/requirements.txt \
    && python3 setup.py install \
    && rm -rf /opt/repairman \
    && rm -rf /var/cache/apk/*

COPY .infrastructure/entrypoint.sh /
ENTRYPOINT ["bash", "/entrypoint.sh"]
HEALTHCHECK --interval=2m CMD curl -k -s -f http://localhost || exit 1

CMD ["repairman"]
