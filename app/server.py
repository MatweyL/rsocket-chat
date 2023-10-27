import asyncio

from rsocket.rsocket_server import RSocketServer
from rsocket.transports.tcp import TransportTCP

from app.handlers import handler_factory, check_online_sessions
from app.logs import logger


class Server:

    def __init__(self, host: str, port: int, handler_factory):
        self._host = host
        self._port = port
        self._handler_factory = handler_factory

    async def run(self):
        def session(*connection):
            RSocketServer(TransportTCP(*connection),
                          handler_factory=self._handler_factory
                          )

        logger.info(f'starting rsocket server at {self._host}:{self._port}')
        async with await asyncio.start_server(session, self._host, self._port) as server:
            await server.serve_forever()


async def main():
    host = 'localhost'
    port = 1875
    server = Server(host, port, handler_factory)
    task = asyncio.create_task(check_online_sessions())
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
