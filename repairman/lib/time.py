
import time as pyTime
import os
import subprocess
import tornado.log


class Time:
    _isTZSet = False

    @staticmethod
    def discover_timezone():
        if Time._isTZSet:
            return

        if os.path.isfile('/etc/timezone'):
            handle = open('/etc/timezone', 'rb')
            os.environ['TZ'] = handle.read().decode('utf-8').strip()
            pyTime.tzset()

            handle.close()
            return

        output = subprocess.check_output('timedatectl|grep "Time zone"', shell=True).decode('utf-8')

        try:
            os.environ['TZ'] = output.split(': ')[1].split(' ')[0]
            pyTime.tzset()

        except KeyError:
            return

    @staticmethod
    def time():
        Time.discover_timezone()
        return pyTime.time()

    @staticmethod
    def sleep(secs):
        Time.discover_timezone()

        tornado.log.app_log.debug('Sleeping ' + str(secs) + ' seconds')
        return pyTime.sleep(secs)


def sleep(secs):
    Time.sleep(secs)


def time():
    return Time.time()
