Configuration
=============

Repairman has two scopes of configuration, internally it's called a policy.
Application policy is a default policy for each container, and a Regular Policy is a per-container policy that mixes Application policy + container specific modifications.

**Example:**

- Application global policy has *time between restarts* equal to 180 and *3 maximum restarts*
- The container can modify some values, ex. will want to have *2 maximum restarts instead of 3 restarts*


Reference
---------

=======================================  ===============================================  ============================================================  ==========================================================
Parameters
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 in shell                                 as docker env variable                            as a docker label                                             description
=======================================  ===============================================  ============================================================  ==========================================================
  --debug                                  NONE                                              NONE                                                          Console debugging mode
  --interval                               CHECK_INTERVAL                                    NONE                                                          How often in seconds to check all containers
  --namespace                              NAMESPACE                                         NONE                                                          Containers prefix (ex. compose env name)
  --seconds-between-restarts               DEFAULT_SECONDS_BETWEEN_RESTARTS                  org.riotkit.repairman.seconds_between_restarts                Seconds to wait until next try
  --frame-size-in-seconds                  DEFAULT_FRAME_SIZE                                org.riotkit.repairman.frame_size_in_seconds                   Frame size (time frame in which max restarts can occur)
  --max-restarts-in-frame                  DEFAULT_MAX_RESTARTS_IN_FRAME                     org.riotkit.repairman.max_restarts_in_frame                   Maximum restarts in given time (frame)
  --seconds-between-next-frame             DEFAULT_SECONDS_BETWEEN_NEXT_FRAME                org.riotkit.repairman.seconds_between_next_frame              Time between frames (for longer wait)
  --max-checks-to-give-up                  DEFAULT_MAX_CHECKS_TO_GIVE_UP                     org.riotkit.repairman.max_checks_to_give_up                   After this number, the service will not be monitored
  --max-historic-entries                   DEFAULT_MAX_HISTORIC_ENTRIES                      org.riotkit.repairman.max_historic_entries                    Technically, how many events to remember
  --enable-cleaning-duplicated-services    ENABLE_CLEANING_DUPLICATED_SERVICES               org.riotkit.repairman.enable_cleaning_duplicated_services     Remove services with hash prefix created by compose
  --enable-autoheal                        DEFAULT_ENABLE_AUTO_HEAL                          org.riotkit.repairman.enable_autoheal                         Enable healing of unhealthy and exited containers
  --http-address                           HTTP_ADDRESS                                      NONE                                                          Web server address ex. 0.0.0.0 or 127.0.0.1
  --http-port                              HTTP_PORT                                         NONE                                                          Web server port ex. 80 or 8080
  --http-prefix                            HTTP_PREFIX                                       NONE                                                          Web server path prefix ex. /something or /SgbaCaVyewq
  --notify-url                             DEFAULT_NOTIFY_URL                                org.riotkit.repairman.notify_url                              Slack/Mattermost notification url
  --notify-level                           DEFAULT_NOTIFY_LEVEL                              org.riotkit.repairman.notify_level                            Notify level ex. DEBUG, INFO, WARNING
  --db-path                                DB_PATH                                           NONE                                                          Path to sqlite3 database or ":memory:"
  NONE                                     TZ                                                NONE                                                          Docker container timezone ex. Europe/Warsaw
  NONE                                     DOCKER_HOST                                       NONE                                                          Docker host address or socket
  NONE                                     DOCKER_TLS_VERIFY                                 NONE                                                          Verify the host against a CA certificate.
  NONE                                     DOCKER_CERT_PATH                                  NONE                                                          Path to directory with certificates
=======================================  ===============================================  ============================================================  ==========================================================

Concept of frames and timing
----------------------------

**Frame** is a time defined by *--frame-size-in-seconds*, ex. 5 minutes. In this time given service can be restarted only *--max-restarts-in-frame*, if it still fails, then it needs to wait *--seconds-between-next-frame* to next restart try.


Cleaning up duplicated services
-------------------------------

When a *v2tec/watchtower* container is updating a service its starting a container with new image version. After compose up, the container is created twice.
The *--enable-cleaning-duplicated-services* resolves this problem by stopping and removing a container with hash prefix.

Changes between restarts
------------------------

Repairman uses SQLite3, by default a in-memory database is used - *:memory:*, but it is not a problem to use a persistent database by changing the *--db-path*

Notifications
-------------

Notifications can be sent to Slack/Mattermost. There are three levels of verbosity. **Do not confuse with --debug**

**Verbosity levels:**

- DEBUG: Each container restart info, maximum restarts limit reached in frame, multiple restart failure info, configuration error
- INFO: Multiple restart failure info, configuration error, maximum restarts limit reached in frame
- WARNING: Configuration error, maximum restarts limit reached in frame

