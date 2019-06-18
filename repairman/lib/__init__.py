
import tornado.log
import time
import logging
import sys
import traceback

from .adapter import Adapter, DockerAdapter
from .journal import Journal
from .tasks import DeduplicationTask, HealTask, Task
from .entity import ApplicationGlobalPolicy
from .http import HttpServer


class Repairman:
    _policy: ApplicationGlobalPolicy
    _journal: Journal
    _adapter: Adapter
    _tasks: list  # type: list[Task]
    _http_address: str
    _http_port: int
    _http_prefix: str

    def __init__(self, params: dict):
        self._http_address = params['http_address']
        self._http_port = params['http_port']
        self._http_prefix = params['http_prefix']

        del params['http_address']
        del params['http_port']
        del params['http_prefix']

        self._policy = ApplicationGlobalPolicy(params)
        self._journal = Journal(self._policy)
        self._adapter = DockerAdapter(self._policy)
        self._tasks = [
            DeduplicationTask(adapter=self._adapter, journal=self._journal),
            HealTask(adapter=self._adapter, journal=self._journal)
        ]

    def main(self):
        """ Main """
        tornado.log.enable_pretty_logging()
        tornado.log.app_log.level = logging.DEBUG if self._policy.debug else logging.INFO
        tornado.log.app_log.info('Docker Repairman is starting...')

        http_server = HttpServer(address=self._http_address, port=self._http_port, server_path_prefix=self._http_prefix)
        http_server.run(lambda: self._journal.get_summary(self._adapter.find_all_containers))

        while True:
            for task in self._tasks:
                try:
                    task.process()
                except:
                    traceback.print_exc(file=sys.stdout)

                time.sleep(self._policy.interval)
