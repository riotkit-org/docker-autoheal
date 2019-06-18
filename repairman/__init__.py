# -*- coding: utf-8 -*-

__author__ = 'Riotkit'
__email__ = 'riotkit_org@riseup.net'
__version__ = '1.0.0'

import argparse
import sys
from lib import Repairman

if __name__ == "__main__":
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
                        default=20)
    parser.add_argument('--frame-size-in-seconds',
                        help='Amount of time for a frame for each service separately ' +
                             '(org.riotkit.repairman.frame_size_in_seconds)',
                        default=300)
    parser.add_argument('--max-restarts-in-frame',
                        help='Maximum count of restarts per frame to mark container as requiring attention ' +
                             '(org.riotkit.repairman.max_restarts_in_frame)',
                        default=5)
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
                        help='Maximum historic entries per container',
                        default=20)
    parser.add_argument('--enable-cleaning-duplicated-services',
                        help='Clear duplicated services after auto-update with watchtower' +
                             ', eg. delete 6e61b61ead5c_iwa_ait_app_sk.nbz.priamaakcia_1 and ' +
                             'keep iwa_ait_app_sk.nbz.priamaakcia_1. ' +
                             '(org.riotkit.repairman.enable_cleaning_duplicated_services)',
                        default=True,
                        action="store_true")

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

    parser.description = 'RiotKit\'s Docker Repair Man'
    parsed = parser.parse_args()

    try:
        Repairman(params=vars(parsed)).main()
    except KeyboardInterrupt:
        print('[CTRL]+[C]')
        sys.exit(0)

