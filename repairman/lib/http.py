
import tornado.ioloop
import tornado.web
import json
import typing
import threading
import asyncio


class MainHandler(tornado.web.RequestHandler):  # pragma: no cover
    callback: typing.Callable

    def _get_limit(self) -> int:
        limit = int(self.get_query_argument('limit', '20'))

        if limit < 1 or limit > 1000:
            limit = 20

        return limit

    def get(self):
        result = MainHandler.callback(self._get_limit())

        self.set_status(500 if not result['global_status'] else 200)
        self.add_header('Content-Type', 'application/json')
        self.write(
            json.dumps(result, sort_keys=True, indent=4, separators=(',', ': '))
        )

    def data_received(self, chunk):
        pass


class HttpServer:  # pragma: no cover
    _port: int
    _path_prefix: str
    _address: str
    _thread: threading.Thread

    def __init__(self, address: str, port: int, server_path_prefix: str):
        self._port = port
        self._address = address
        self._path_prefix = server_path_prefix

    def run(self, callback: typing.Callable):
        self._thread = threading.Thread(target=lambda: self._run(callback))
        self._thread.setDaemon(True)
        self._thread.start()

    def _run(self, callback: typing.Callable):
        MainHandler.callback = callback

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        srv = tornado.web.Application([(r"" + self._path_prefix + "/", MainHandler)])
        srv.listen(self._port, self._address)
        loop.run_forever()
