Quick start
===========

Using docker container
----------------------

**Official docker container is:** *quay.io/riotkit/repairman*

Using docker-compose we can define a clean, easy to read YAML file:

.. code:: yaml

    version: "2"
    services:
        autoheal:
            image: quay.io/riotkit/repairman
            environment:
                NAMESPACE: aarchive
                DEFAULT_SECONDS_BETWEEN_RESTARTS: 15
                DEFAULT_FRAME_SIZE: 450
                DEFAULT_MAX_RESTARTS_IN_FRAME: 3
                DEFAULT_SECONDS_BETWEEN_NEXT_FRAME: 1500
                DEFAULT_MAX_CHECKS_TO_GIVE_UP: 50
                DEFAULT_MAX_HISTORIC_ENTRIES: 50
                DEFAULT_ENABLE_DUPLICATED_SERVICES_REMOVING: "true"
                DEFAULT_ENABLE_AUTO_HEAL: "true"
                TZ: Europe/Warsaw
                DEFAULT_NOTIFY_LEVEL: debug
                DEFAULT_NOTIFY_URL: ""
            restart: always
            mem_limit: 80000000 # 80M, 30M is the average
            volumes:
                - /var/run/docker.sock:/var/run/docker.sock
            labels:
                com.centurylinklabs.watchtower.enable: true
                org.riotkit.repairman.enable_autoheal: false


.. code:: bash

    # running with all default values
    sudo docker run -v /var/run/docker.sock:/var/run/docker.sock wolnosciowiec/repairman:latest

    # using environment variables to configure
    sudo docker run -e DEFAULT_FRAME_SIZE=450 -v /var/run/docker.sock:/var/run/docker.sock wolnosciowiec/repairman:latest

    # using console switches
    sudo docker run -e DEFAULT_FRAME_SIZE=450 -v /var/run/docker.sock:/var/run/docker.sock wolnosciowiec/repairman:latest --debug --enable-autoheal


Building and installing a Python package
----------------------------------------

.. code:: bash

    git clone https://github.com/riotkit-org/docker-autoheal
    cd docker-autoheal
    make install


Building a docker image
-----------------------

.. code:: bash

    git clone https://github.com/riotkit-org/docker-autoheal
    cd docker-autoheal
    make build_image


Installing with Python PIP
--------------------------

.. code:: bash

    sudo pip install repairman
    repairman --help

