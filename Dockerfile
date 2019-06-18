ARG arch=x86_64
FROM multiarch/alpine:${arch}-v3.9

COPY ./ /opt/repairman
COPY docker-entrypoint /

RUN apk add --no-cache curl jq python3 bash \
    && cd /opt/repairman \
    && pip install -i ./requirements.txt \
    && python3 setup.py install \
    && rm -rf /opt/repairman

ENTRYPOINT ["/entrypoint.sh"]
HEALTHCHECK --interval=5s CMD curl -k -s -f http://localhost || exit 1

CMD ["repairman"]
