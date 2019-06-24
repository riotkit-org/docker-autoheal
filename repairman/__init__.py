# -*- coding: utf-8 -*-

__author__ = 'Riotkit'
__email__ = 'riotkit_org@riseup.net'
__version__ = '1.0.0'

import argparse
import sys
import traceback

try:
    from lib import Repairman
    from lib.exception import ConfigurationException

except ImportError:
    from .lib import Repairman
    from .lib.exception import ConfigurationException


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', help='Prints debugging messages', default=False, action="store_true")
    parser.add_argument('--interval',
                        help='How often in seconds check all containers?',
                        default=120)
    parser.add_argument('--namespace',
                        help='Docker containers name prefix',
                        default='')

    # Services default configuration
    parser.add_argument('--seconds-between-restarts',
                        help='Time to wait between restarts to give a next try ' +
                             '(org.riotkit.repairman.seconds_between_restarts)',
                        default=15)
    parser.add_argument('--frame-size-in-seconds',
                        help='Amount of time for a frame for each service separately ' +
                             '(org.riotkit.repairman.frame_size_in_seconds)',
                        default=450)
    parser.add_argument('--max-restarts-in-frame',
                        help='Maximum count of restarts per frame to mark container as requiring attention ' +
                             '(org.riotkit.repairman.max_restarts_in_frame)',
                        default=3)
    parser.add_argument('--seconds-between-next-frame',
                        help='Seconds to wait to perform a repair again after reaching maximum retries ' +
                             '(org.riotkit.repairman.seconds_between_next_frame)',
                        default=3600)
    parser.add_argument('--max-checks-to-give-up',
                        help='Maximum count of checks to give up and ' +
                             'mark the container as not recoverable automatically ' +
                             '(org.riotkit.repairman.max_checks_to_give_up)',
                        default=10)
    parser.add_argument('--max-historic-entries',
                        help='Maximum historic entries per container (org.riotkit.repairman.max_historic_entries)',
                        default=20)
    parser.add_argument('--enable-cleaning-duplicated-services',
                        help='Clear duplicated services after auto-update with watchtower' +
                             ', eg. delete 6e61b61ead5c_iwa_ait_app_sk.nbz.priamaakcia_1 and ' +
                             'keep iwa_ait_app_sk.nbz.priamaakcia_1. ' +
                             '(org.riotkit.repairman.enable_cleaning_duplicated_services)',
                        default=True,
                        action='store_true')
    parser.add_argument('--enable-autoheal',
                        help='By default enable auto-healing for all services ' +
                             '(org.riotkit.repairman.enable_autoheal)',
                        default=True,
                        action='store_true')

    # HTTP
    parser.add_argument('--http-address',
                        help='HTTP Server address',
                        default='0.0.0.0')
    parser.add_argument('--http-port',
                        help='HTTP Server port',
                        default=8080)
    parser.add_argument('--http-prefix',
                        help='HTTP endpoint prefix (security)',
                        default='')

    # Notify URL
    parser.add_argument('--notify-url',
                        help='Notification URL (Slack/Mattermost compatible) (org.riotkit.repairman.notify_url)',
                        default='')

    parser.add_argument('--notify-level',
                        help='Notification level: DEBUG, INFO, ERROR (org.riotkit.repairman.notify_level)',
                        default='INFO')

    parser.add_argument('--db-path',
                        help='Can allow to persist database into file, defaults to ":memory:" which ' +
                             'will not keep changes between restarts',
                        default=':memory:')

    parser.description = 'RiotKit\'s Docker Repair Man'
    parsed = parser.parse_args()

    try:
        Repairman(params=vars(parsed)).main()

    except ConfigurationException as e:
        traceback.print_exc(file=sys.stdout)

    except KeyboardInterrupt:
        print('[CTRL]+[C]')
        sys.exit(0)


if __name__ == "__main__":
    main()

