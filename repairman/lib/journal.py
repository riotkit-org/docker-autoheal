

from .entity import Container
from .entity import ApplicationGlobalPolicy
import sqlite3
import threading
import typing
import tornado.log


class Journal:
    """ Stores information about containers """

    _EVENT_TYPE_RESTART = 'restart'
    _EVENT_TYPE_MAX_RESTARTS = 'restart.max-reached'
    _EVENT_TYPE_DNT = 'do-not-touch-anymore'

    db: sqlite3.Connection
    cur: sqlite3.Cursor
    app_policy: ApplicationGlobalPolicy
    lock: threading.Lock

    def __init__(self, policy: ApplicationGlobalPolicy):
        self.db = sqlite3.connect(policy.db_path, check_same_thread=False)
        self.app_policy = policy
        self.cur = self.db.cursor()
        self.lock = threading.Lock()
        self._migrate()

    def _find_events(self, container_name: str, event_type: str, time_modifier_to_start_from: str,
                     archived: bool = False) -> list:

        archived_str = ''

        if not archived:
            archived_str = 'AND archived is null'

        result = self._fetch_all(
            '''
                SELECT datetime(event_date, 'localtime'), datetime(datetime("now", ?), 'localtime'), journal.*
                FROM journal 
                WHERE 
                    event_type = ?
                    AND datetime(event_date, 'localtime') >= datetime(datetime("now", ?), 'localtime')
                    AND container_name = ?
                    ''' + archived_str + '''
            ''',
            [
                time_modifier_to_start_from,
                event_type,
                time_modifier_to_start_from,
                container_name
            ]
        )

        tornado.log.app_log.debug('_find_events(' + container_name + ', ' + event_type + ', ' +
                                  time_modifier_to_start_from + ')')
        tornado.log.app_log.debug(str(result))

        return result

    def get_total_restart_count_in_all_frames(self, container: Container) -> int:
        result = self._fetch_one(
            '''
                SELECT COUNT(id)
                FROM journal
                WHERE 
                    container_name = ? AND event_type = ?
            ''',
            [
                container.get_name(), self._EVENT_TYPE_RESTART
            ]
        )

        return int(result[0])

    def find_restart_count_in_frame(self, container: Container) -> int:
        return len(self._find_events(container.get_name(), self._EVENT_TYPE_RESTART,
                   '-' + str(container.policy.frame_size_in_seconds) + ' seconds'))

    def find_reached_max_restarts_in_previous_frame(self, container: Container) -> bool:
        return len(self._find_events(container.get_name(), self._EVENT_TYPE_MAX_RESTARTS,
                   '-' + str(container.policy.frame_size_in_seconds * 2) + ' seconds', archived=True)) > 0

    def find_last_restart_time(self, container: Container) -> int:
        result = self._fetch_one(
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

        if not result:
            return 0

        return int(result[0])

    def _migrate(self):
        try:
            self._exec(
                '''
                    CREATE TABLE journal (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        container_name TEXT, 
                        event_type TEXT, 
                        event_date TEXT, 
                        message TEXT,
                        archived BOOLEAN
                    );
                '''
            )
        except sqlite3.OperationalError:
            # the table can already exist in case, when the database file is persistable
            pass

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

    def get_summary(self, callback: typing.Callable, last_events_limit: int) -> dict:
        failing = self._find_failing(callback())

        return {
            'last_events': self._find_last_events(last_events_limit),
            'constantly_failing': failing,
            'constantly_failing_count': len(failing),
            'global_status': len(failing) == 0
        }

    def _find_failing(self, containers: list) -> list:
        failing = []

        for container in containers:
            if container.policy.max_restarts_in_frame == 0:
                continue

            restart_count_in_frame = self.find_restart_count_in_frame(container)
            reached_max_restarts_in_previous_frame = self.find_reached_max_restarts_in_previous_frame(container)

            # first condition: now already reached max restarts in frame
            # second condition: still failing, whole previous frame failed, in current frame we have at least
            #  1 check failing

            if restart_count_in_frame > container.policy.max_restarts_in_frame \
                    or (restart_count_in_frame > 0 and reached_max_restarts_in_previous_frame):
                failing.append({
                    'id': container.get_name(),
                    'ident': container.get_name() + '=False',
                    'restarts_in_current_frame': restart_count_in_frame,
                    'reached_max_in_previous_frame': reached_max_restarts_in_previous_frame
                })

        return failing

    def _find_last_events(self, limit: int = 20):
        events = self._fetch_all(
            '''
                SELECT 
                    message, 
                    container_name as container, 
                    event_date as time, 
                    id as num 
                FROM journal
                ORDER BY id DESC LIMIT 0, ?
            ''',
            [limit]
        )

        return list(map(
            lambda row: {
                'date': row[2],
                'message': row[0],
                'container': row[1],
                'num': row[3]
            },
            events
        ))

    def find_is_marked_as_not_touch(self, container: Container):
        events = self._fetch_one(
            '''
                SELECT COUNT(id)
                FROM journal
                WHERE 
                    container_name = ? AND event_type = ?
            ''',
            [
                container.get_name(), self._EVENT_TYPE_DNT
            ]
        )

        return int(events[0]) > 0

    def clear_all_container_history(self, container: Container):
        self._exec(
            '''
                DELETE FROM journal WHERE container_name = ?
            ''',
            [container.get_name()]
        )

    def _mark_all_events_as_archived(self, container: Container):
        self._exec(
            '''
                UPDATE journal SET archived = 1 WHERE container_name = ?
            ''',
            [container.get_name()]
        )

    def record_max_restarts_reached_and_waited(self, container: Container):
        self._mark_all_events_as_archived(container)
        self._record_event(container, self._EVENT_TYPE_MAX_RESTARTS,
                           'Starting next frame after max restarts reached and wait time')

    def record_do_not_touch(self, container: Container) -> bool:
        """ Returns success when the service was just now marked as "DO NOT TOUCH" """

        # do not spam with events
        if self.find_is_marked_as_not_touch(container):
            return False

        self._record_event(container, self._EVENT_TYPE_DNT, 'Maximum restarts reached, not touching anymore')
        return True

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

    def __query(self, sql: str, params=None) -> sqlite3.Cursor:
        if params is None:
            params = []

        exec_sql = self.cur.execute(sql, params)

        # tornado.log.app_log.debug(sql)

        self.db.commit()

        return exec_sql

    def _exec(self, sql: str, params=None) -> None:
        self.lock.acquire()
        try:
            self.__query(sql, params)
        finally:
            self.lock.release()

    def _fetch_one(self, sql: str, params=None):
        self.lock.acquire()

        try:
            result = self.__query(sql, params).fetchone()
        finally:
            self.lock.release()

        return result

    def _fetch_all(self, sql: str, params=None):
        self.lock.acquire()

        result = self.__query(sql, params).fetchall()
        self.lock.release()

        return result
