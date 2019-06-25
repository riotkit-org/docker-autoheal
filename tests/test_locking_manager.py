import unittest
import sys
import os
import inspect
import mock

path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/../'
sys.path.append(path)

try:
    from ..repairman.lib.semaphore import LockingManager
    from ..repairman.lib.exception import ContainerIsLocked
except ImportError:
    from repairman.lib.semaphore import LockingManager
    from repairman.lib.exception import ContainerIsLocked


class ControllerTest(unittest.TestCase):

    def test_is_locking(self):
        """ Checks if the resource is really locked and throws an exception on next locking try """

        container = mock.Mock()
        container.configure_mock(**{'identify': lambda: 'Hello, International Workers Association!'})

        manager = LockingManager()
        manager.acquire(container)
        was_thrown = False

        try:
            manager.acquire(container)
        except ContainerIsLocked:
            was_thrown = True

        self.assertTrue(was_thrown, 'Expected that a ContainerIsLocked exception will be thrown')

    def test_is_releasing(self):
        """ Check if the flow of ACK->RELEASE works """

        container = mock.Mock()

        manager = LockingManager()
        manager.acquire(container)
        manager.release(container)
        manager.acquire(container)
        manager.release(container)

        self.assertTrue(True)
