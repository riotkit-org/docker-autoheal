
RiotKit's Repairman
===================

Keeps an eye on unhealthy and exited containers. Provides Kubernetes-like functionality to non-Kubernetes environments.

Works with docker, docker-compose, in future can possibly work without an issue with any clusters or even on RKT, LXC and others.

**Features:**

- Automatic restart of unhealthy containers
- Configurable wait time between container restarts
- Maximum restarts in configured time, after that configured longer wait time
- Removing of duplicated services created with hash-prefixes by docker-compose (ex. after watchtower update)
- Notifications to Slack/Mattermost (with configurable levels: DEBUG, INFO, WARNING)
- Configured default settings via environment variables or console switches
- Each service can override default configuration using Docker Labels
- Lightweight and independent! Provides Kubernetes-like functionality to non-Kubernetes environments
- Can run as a docker container
- Health check endpoint

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quick_start
   reference

From authors
============

Project was started as a part of RiotKit initiative, for the needs of grassroot organizations such as:

- Fighting for better working conditions syndicalist (International Workers Association for example)
- Tenants rights organizations
- Various grassroot organizations that are helping people to organize themselves without authority

.. rst-class:: language-en align-center

*RiotKit Collective*
