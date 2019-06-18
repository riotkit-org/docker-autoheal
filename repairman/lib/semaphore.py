
import time
from .entity import Container
from .exception import ContainerIsLocked


class LockingManager:
    _locks = {}
    _max_lock_lifetime = 3600

    def acquire(self, container: Container):
        is_locked = container.identify() in self._locks

        if is_locked and time.time() >= self._locks[container.identify()]:
            self.release(container)

        if is_locked:
            raise ContainerIsLocked('"' + container.identify() + '" already locked')

        self._locks[container.identify()] = time.time() + self._max_lock_lifetime

    def release(self, container: Container):
        try:
            del self._locks[container.identify()]
        except KeyError:
            pass
