import logging
from typing import Union

import jsonschema
from aiohttp.web import Application, Request, Response, json_response, \
    HTTPNotFound

from neighbour_seeker import db, validators

logger = logging.getLogger(__name__)


async def get_user_row(request: Request, user_id: int) -> Union[Response, dict]:
    """ Get user DB row, raise 404 if not found. """
    async with request.app['db_pool'].acquire() as conn:
        user_row = await db.get_user(conn, user_id)
    if not user_row:
        logger.warning('User %s not found', user_id)
        raise HTTPNotFound(text='User not found')
    return user_row


async def get_user(request: Request) -> Response:
    """ Get user info by id. """
    user_id = validators.validate_user_id(request.match_info['user_id'])
    user_info = dict(await get_user_row(request, user_id))
    if not user_info['description']:
        user_info.pop('description')
    return json_response(data=user_info, status=200)


@validators.validate_json
async def create_user(request: Request) -> Response:
    """ Create a single user. """
    payload = await request.json()
    jsonschema.validate(payload, validators.user_schema)
    name, latitude, longitude, description = \
        payload['name'], payload['latitude'], \
        payload['longitude'], payload.get('description')
    async with request.app['db_pool'].acquire() as conn:
        user_id = await db.create_user(conn, name, latitude, longitude, description)
    response_data = {'user_id': user_id}
    return json_response(data=response_data, status=201)


@validators.validate_json
async def update_user(request: Request) -> Response:
    """ Update user information: name, description, coords. """
    user_id = validators.validate_user_id(request.match_info['user_id'])
    await get_user_row(request, user_id)
    payload = await request.json()
    jsonschema.validate(payload, validators.user_schema)

    # all update fields must be present
    name, latitude, longitude, description = \
        payload['name'], payload['latitude'], \
        payload['longitude'], payload.get('description')
    async with request.app['db_pool'].acquire() as conn:
        await db.update_user(conn, name, latitude, longitude, description, user_id)
    return json_response(status=200)


async def delete_user(request: Request) -> Response:
    """ Delete a user by id. """
    user_id = validators.validate_user_id(request.match_info['user_id'])
    await get_user_row(request, user_id)
    async with request.app['db_pool'].acquire() as conn:
        await db.delete_user(conn, user_id)
    return json_response(status=200)


@validators.validate_json
async def search(request: Request) -> Response:
    """ Perform KNN search returning nearest neighbour user ids. """
    payload = await request.json()
    jsonschema.validate(payload, validators.search_schema)
    user_id, distance, count = \
        payload['user_id'], payload['distance'], payload['count']
    await get_user_row(request, user_id)
    # kilometers to meters
    distance *= 1000
    async with request.app['db_pool'].acquire() as conn:
        results = await db.search(conn, user_id, distance, count)
    return json_response(data=results, status=200)


def setup_routes(app: Application) -> None:
    """ Register http application handlers. """
    app.router.add_get('/users/{user_id}', get_user)
    app.router.add_post('/users', create_user)
    app.router.add_put('/users/{user_id}', update_user)
    app.router.add_delete('/users/{user_id}', delete_user)
    app.router.add_post('/search', search)
    logger.info('App routes initialized')
