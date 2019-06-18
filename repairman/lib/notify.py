
import requests
import tornado.log
import traceback
import json
import sys
from .entity import Container


class Notify:
    _DEBUG = 3
    _INFO = 2
    _ERROR = 1

    _PRIORITIES = {
        'DEBUG': 3,
        'INFO': 2,
        'ERROR': 1
    }

    def container_was_removed(self, container: Container):
        self._send(container, '[:warning:] Container was removed', self._DEBUG)

    def container_was_restarted(self, container: Container, log: str):
        self._send(container, '[:warning:] Container was restarted', self._DEBUG, log)

    def max_restarts_reached(self, container: Container, log: str):
        self._send(container, '[:exclamation:] Max restarts reached, will wait longer till next try', self._ERROR, log)

    def multiple_failures_happened(self, container: Container, log: str):
        self._send(container, '[:exclamation:] Multiple restart failures happened', self._INFO, log)

    def _send(self, container: Container, message: str, priority: int, log: str = ''):
        if self._resolve_priority(container.policy.notify_level) < priority:
            return

        if not container.policy.notify_url:
            return

        formatted_log = ''

        if log:
            formatted_log = "\n\n```\n" + log + "\n```"

        try:
            requests.post(container.policy.notify_url, data=json.dumps({
                'text': '**' + container.get_name() + ':** ' + message + formatted_log
            }))
        except:
            traceback.print_exc(file=sys.stdout)
            tornado.log.app_log.warn('Unable to post a notification to "' + container.policy.notify_url + '"')

    def _resolve_priority(self, priority: str) -> int:
        priority = priority.strip().lower()

        if priority not in self._PRIORITIES:
            return 3

        return self._PRIORITIES[priority]