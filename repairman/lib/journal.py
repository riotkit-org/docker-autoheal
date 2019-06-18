
from .entity import Container
from .entity import ApplicationGlobalPolicy
import sqlite3
import threading
import typing


class Journal:
    """ Stores information about containers """

    _EVENT_TYPE_RESTART = 'restart'

    db: sqlite3.Connection
    cur: sqlite3.Cursor
    app_policy: ApplicationGlobalPolicy
    lock: threading.Lock

    def __init__(self, policy: ApplicationGlobalPolicy):
        self.db = sqlite3.connect(':memory:', check_same_thread=False)
        self.app_policy = policy
        self.cur = self.db.cursor()
        self.lock = threading.Lock()
        self._migrate()

    def find_restart_count_in_frame(self, container: Container):
        q = self._exec(
            '''
                SELECT COUNT(container_name)
                FROM journal 
                WHERE 
                    event_type = ?
                    AND datetime(event_date) >= datetime("now", ?)
                    AND container_name = ?
            ''',
            [
                self._EVENT_TYPE_RESTART,
                '-' + str(container.policy.frame_size_in_seconds) + ' seconds',
                container.get_name()
             ]
        )

        return q.fetchone()[0]

    def find_last_restart_time(self, container: Container) -> int:
        q = self._exec(
            '''
                SELECT strftime("%s", event_date)
                FROM journal
                WHERE
                    event_type = ?
                    AND container_name = ?
                ORDER BY id DESC
                LIMIT 0, 1
            ''',
            [self._EVENT_TYPE_RESTART, container.get_name()]
        )

        result = q.fetchone()

        if not result:
            return 0

        return int(result[0])

    def _migrate(self):
        self._exec(
            '''
                CREATE TABLE journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    container_name TEXT, 
                    event_type TEXT, 
                    event_date TEXT, 
                    message TEXT
                    );
            '''
        )

    def _rotate_events(self, container: Container):
        self._exec(
            '''
                DELETE FROM journal WHERE container_name = ?
                AND id not in (
                    SELECT id FROM journal WHERE container_name = ?
                    ORDER BY id DESC LIMIT 0, ?
                )
            ''',
            [
                container.get_name(),
                container.get_name(),
                self.app_policy.max_historic_entries
            ]
        )

    def get_summary(self, callback: typing.Callable) -> dict:
        failing = self._find_failing(callback())

        return {
            'last_events': self._find_last_events(),
            'find_failing': failing,
            'failing_count': len(failing),
            'global_status': len(failing) > 0
        }

    def _find_failing(self, containers: list) -> list:
        failing = []

        for container in containers:
            restart_count_in_frame = self.find_restart_count_in_frame(container)

            if restart_count_in_frame > container.policy.max_restarts_in_frame:
                failing.append({
                    'id': container.get_name(),
                    'ident': container.get_name() + '=False',
                    'restarts': restart_count_in_frame
                })

        return failing

    def _find_last_events(self):
        q = self._exec(
            '''
                SELECT 
                    message, 
                    container_name as container, 
                    event_date as time, 
                    id as num 
                FROM journal
                ORDER BY id DESC LIMIT 0, 20
            '''
        )

        return list(map(
            lambda row: {
                'date': row[2],
                'message': row[0],
                'container': row[1],
                'num': row[3]
            },
            q.fetchall()
        ))

    def record_restart(self, container: Container):
        self._record_event(container, self._EVENT_TYPE_RESTART, 'Container was restarted')

    def _record_event(self, container: Container, event_type: str, message: str):
        self._rotate_events(container)
        self._exec(
            '''
                INSERT INTO journal (container_name, event_type, event_date, message)
                VALUES (?, ?, datetime('now'), ?);
            ''',
            [
                container.get_name(),
                event_type,
                message
            ]
        )

    def _exec(self, sql, params=None) -> sqlite3.Cursor:
        if params is None:
            params = []

        try:
            self.lock.acquire()

            return self.cur.execute(sql, params)
        finally:
            self.lock.release()
