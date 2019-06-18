
from .adapter import Adapter
from .journal import Journal
from .entity import Container
from .exception import ContainerIsLocked
from .semaphore import LockingManager
from .notify import Notify
import threading
import tornado.log
import time
import abc
import traceback
import sys


class Task(metaclass=abc.ABCMeta):
    _lock_manager: LockingManager
    _notify: Notify

    _adapter: Adapter
    _journal: Journal
    _threads = []

    def __init__(self, adapter: Adapter, journal: Journal):
        self._adapter = adapter
        self._journal = journal
        self._lock_manager = LockingManager()
        self._notify = Notify()

    @abc.abstractmethod
    def process(self):
        pass


class DeduplicationTask(Task):
    def process(self):
        all_in_network = self._adapter.find_all_containers_in_namespace()
        all_containers = self._adapter.find_all_containers()
        mapped = {}

        for container in all_containers:
            mapped[container.get_name()] = container

        for container in all_in_network:
            name = container.get_name()
            name_length_with_duplication_prefix = len(name) + 13

            if not container.policy.enable_cleaning_duplicated_services:
                continue

            for other_name, other_container in mapped.items():
                # at first validate first part
                split = other_name.split('_')

                if len(split[0]) != 12:
                    continue

                if other_name.endswith('_' + name) and len(other_name) == name_length_with_duplication_prefix:
                    try:
                        self._lock_manager.acquire(container)
                        thread = threading.Thread(
                            target=lambda:
                                self._process_container(other_container, container)
                                or self._lock_manager.release(container)
                        )
                        thread.setDaemon(True)
                        self._threads.append(thread)
                        thread.start()
                    except ContainerIsLocked:
                        pass
                    except:
                        self._lock_manager.release(container)
                        traceback.print_exc(file=sys.stdout)

    def _process_container(self, duplicated: Container, container: Container):
        """ Threaded method """
        tornado.log.app_log.warn('Stopping and removing container "' + duplicated.get_name() + '", it\'s a ' +
                                 'duplication of "' + container.get_name() + '"')

        self._adapter.remove_container(duplicated.get_name())
        self._notify.container_was_removed(duplicated)


class HealTask(Task):
    _POLICY_WAIT = 'wait'
    _POLICY_RESTART = 'restart'
    _POLICY_DO_NOT_TOUCH = 'dnt'
    _POLICY_LONGER_WAIT = 'long_wait'

    def process(self):
        unhealthy = self._adapter.find_all_unhealthy_containers_in_namespace()

        for container in unhealthy:
            try:
                self._lock_manager.acquire(container)
                thread = threading.Thread(
                    target=lambda: self._process_container(container) or self._lock_manager.release(container)
                )
                thread.setDaemon(True)
                self._threads.append(thread)
                thread.start()

            except ContainerIsLocked:
                pass
            except:
                traceback.print_exc(file=sys.stdout)

    def _process_container(self, container: Container):
        """ Process method for a container, executes IN A THREAD """

        tornado.log.app_log.debug('Preparing to restart container "' + container.get_name() + '"')
        policy = self._find_out_what_to_do_with_container(container)

        if policy == self._POLICY_DO_NOT_TOUCH:
            tornado.log.app_log.info('Will not restart "' + container.get_name() + '"')
            return

        if isinstance(policy, int):
            tornado.log.app_log.warn('Waiting for container "' + container.get_name() + '" before next restart')
            self._notify.multiple_failures_happened(container, self._adapter.get_log(container.get_name()))
            time.sleep(policy)

        if policy == self._POLICY_LONGER_WAIT:
            tornado.log.app_log.error('Maximum restarts reached for "' + container.get_name() + '". ' +
                                      'Waiting a bit longer (' + str(container.policy.seconds_between_next_frame) + 's)')
            self._notify.max_restarts_reached(container, self._adapter.get_log(container.get_name()))
            time.sleep(container.policy.seconds_between_next_frame)

        tornado.log.app_log.info('Sending restart signal for "' + container.get_name() + '"')
        self._journal.record_restart(container)
        self._adapter.restart_container(container.get_name())
        self._notify.container_was_restarted(container, self._adapter.get_log(container.get_name()))

    def _find_out_what_to_do_with_container(self, container: Container):
        """ Policy method, decides if we can restart the container NOW or if we wait a little bit """

        restart_count = self._journal.find_restart_count_in_frame(container)
        last_restart_time = self._journal.find_last_restart_time(container)

        if restart_count > container.policy.max_restarts_in_frame:
            return self._POLICY_LONGER_WAIT

        if last_restart_time + container.policy.seconds_between_restarts > time.time():
            return (last_restart_time + container.policy.seconds_between_restarts) - time.time()

        return self._POLICY_RESTART

