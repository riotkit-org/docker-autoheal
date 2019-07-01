
import requests
import tornado.log
import traceback
import json
import sys
from .entity import Container
from .entity import ApplicationGlobalPolicy


class Notify:
    _DEBUG = 3
    _INFO = 2
    _ERROR = 1

    _PRIORITIES = {
        'DEBUG': 3,
        'INFO': 2,
        'ERROR': 1
    }

    app_policy: ApplicationGlobalPolicy

    def __init__(self, app_policy: ApplicationGlobalPolicy):
        self.app_policy = app_policy

    def container_was_removed(self, container: Container):
        self._send(container, '[:warning:] Container was removed', self._DEBUG)

    def container_was_restarted(self, container: Container, log: str):
        self._send(container, '[:warning:] Container was restarted', self._DEBUG, log)

    def container_is_back_to_alive(self, container: Container):
        self._send(container, '[:sunglasses:] Container is healthy now', self._INFO)

    def max_restarts_reached(self, container: Container, log: str):
        self._send(container, '[:exclamation:] Max restarts reached, will wait longer till next try', self._ERROR, log)

    def multiple_failures_happened(self, container: Container, log: str):
        self._send(container, '[:exclamation:] Multiple restart failures happened', self._INFO, log)

    def not_touching_anymore(self, container: Container):
        self._send(container,
                   '[:exclamation: :exclamation: :exclamation:] Admin, help. I\'m not touching the container ' +
                   'anymore. Max restarts reached.',
                   self._INFO)

    def container_configuration_invalid(self, container: Container, message: str):
        self._send(container, '[:exclamation:] Container configuration error: ' + message, self._ERROR)

    def any_container_configuration_invalid(self, message: str):
        if not self.app_policy.notify_url:
            return

        self._send_plain(self.app_policy.notify_url,
                         '[:exclamation:] At least one container has invalid configuration: ' + message)

    def _send(self, container: Container, message: str, priority: int, log: str = ''):
        if self._resolve_priority(container.policy.notify_level) < priority:
            return

        if not container.policy.notify_url:
            return

        formatted_log = ''

        if log:
            formatted_log = "\n\n```\n" + log + "\n```"

        self._send_plain(container.policy.notify_url, '**' + container.get_name() + ':** ' + message + formatted_log)

    def _send_plain(self, url: str, text: str):
        try:
            requests.post(url, data=json.dumps({
                'text': text
            }))
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            tornado.log.app_log.warn('Unable to post a notification to "' + url + '". ' + str(e))

    def _resolve_priority(self, priority: str) -> int:
        priority = priority.strip().upper()

        if priority not in self._PRIORITIES:
            return 3

        return self._PRIORITIES[priority]