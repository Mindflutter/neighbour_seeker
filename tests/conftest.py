from unittest import mock

import pytest
from aiohttp import web
from asynctest import CoroutineMock

from neighbour_seeker.routes import setup_routes


# xxx: this seems too hacky
class AsyncContextManager(mock.MagicMock):

    async def __aenter__(self, *args, **kwargs):
        return self.__enter__(*args, **kwargs)

    async def __aexit__(self, *args, **kwargs):
        return self.__exit__(*args, **kwargs)


@pytest.fixture
def client(loop, aiohttp_client, monkeypatch):
    app = web.Application()
    setup_routes(app)
    app['db_pool'] = CoroutineMock()
    monkeypatch.setattr(app['db_pool'], 'acquire', AsyncContextManager)
    return loop.run_until_complete(aiohttp_client(app))
