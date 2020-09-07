import asyncio
import logging
import sys
from typing import Optional

from aiohttp.web import Application
from asyncpg import create_pool, connection
from asyncpg.exceptions import ConnectionDoesNotExistError
from asyncpg.pool import Pool

from neighbour_seeker import config

logger = logging.getLogger(__name__)


async def get_db_pool() -> Pool:
    """ DB related initialization: connection pool. """
    tries = 0
    while tries < 10:
        try:
            pool = await create_pool(dsn=config.PG_DSN, max_size=config.PG_POOL_SIZE, timeout=30)
            return pool
        except (OSError, ConnectionDoesNotExistError):
            logger.info('Waiting for DB')
            await asyncio.sleep(2 ** tries)
            tries += 1
    # love the pun here
    logger.error('Awaited DB connection for too long, shutting down')
    sys.exit('DB connection error')


async def init_db(app: Application) -> None:
    """ DB related initialization: table, index. """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute('create table if not exists users'
                           ' (id serial primary key, name varchar(64),'
                           ' description varchar(256), location geometry(point))')
        await conn.execute('create index if not exists users_idx on users using gist(location)')
    app['db_pool'] = pool
    logger.info('DB initialized')


async def close_db(app: Application) -> None:
    """ Tear down DB pool. """
    await app['db_pool'].close()
    logger.info('DB pool closed')


async def get_user(conn: connection, user_id: int) -> Optional[dict]:
    """ Get user info from DB. """
    logger.debug('Fetching info for user %s', user_id)
    query = 'select name, description, ST_X(location) longitude, ' \
            'ST_Y(location) latitude from users where id = $1'
    user_row = await conn.fetchrow(query, user_id)
    return user_row if user_row else None


async def create_user(conn: connection,
                      name: str,
                      latitude: float,
                      longitude: float,
                      description: str) -> int:
    """ Insert new user into DB. """
    logger.debug('Inserting user: name %s, coords %s %s, description %s',
                 name, latitude, longitude, description)
    query = 'insert into users (name, description, location)' \
            ' values ($1, $2, ST_MakePoint($3, $4)) returning id'
    # note: longitude as x, latitude as y
    user_id = await conn.fetchval(query, name, description, longitude, latitude)
    return user_id


async def update_user(conn: connection,
                      name: str,
                      latitude: float,
                      longitude: float,
                      description: str,
                      user_id: int) -> None:
    """ Update user info in DB. All fields must be present. None turns into null. """
    logger.debug('Updating user %s: name %s, coords %s %s, description %s',
                 user_id, name, latitude, longitude, description)
    query = 'update users set name = $1, description = $2,' \
            ' location = ST_MakePoint($3, $4) where id = $5'
    await conn.execute(query, name, description, longitude, latitude, user_id)


async def delete_user(conn: connection, user_id: int) -> None:
    """ Delete user from DB by id. """
    logger.debug('Deleting user %s', user_id)
    query = 'delete from users where id = $1'
    await conn.execute(query, user_id)


async def search(conn: connection,
                 user_id: int,
                 distance: float,
                 count: int) -> list:
    """
    KNN search.
    Uses cartesian distance when sorting, sphere distance when comparing.
    Fast index scans at a cost of slight inaccuracy.
    """
    logger.debug('Searching %s nearest neighbours for user %s within %s meters',
                 count, user_id, distance)
    query = 'select id from users where ST_DistanceSphere(location,' \
            ' (select location from users where id = $1)) < $2 and id != $1' \
            ' order by location <-> (select location from users where id = $1) limit $3'
    results = await conn.fetch(query, user_id, distance, count)
    return [result['id'] for result in results]
