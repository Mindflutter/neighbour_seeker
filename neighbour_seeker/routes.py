import logging

import jsonschema
from aiohttp.web import Application, Request, Response, json_response, \
    HTTPNotFound, HTTPBadRequest

from neighbour_seeker import db, validators

logger = logging.getLogger(__name__)


async def get_user(request: Request) -> Response:
    """ Get user info by id. """
    try:
        user_id = int(request.match_info['user_id'])
    except ValueError:
        logger.error('Passed wrong user id: "%s", must be integer',
                     request.match_info['user_id'])
        raise HTTPBadRequest(text='User id must be integer')
    async with request.app['db_pool'].acquire() as conn:
        user_info = await db.get_user(conn, user_id)
    if not user_info:
        logger.warning('User %s not found', user_id)
        raise HTTPNotFound(text='User not found')
    return json_response(data=user_info, status=200)


@validators.validate_json
async def create_user(request: Request) -> Response:
    """ Create a single user. """
    payload = await request.json()
    jsonschema.validate(payload, validators.create_user_schema)
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
    user_id = int(request.match_info['user_id'])
    payload = await request.json()
    jsonschema.validate(payload, validators.update_user_schema)

    # all update fields must be present
    name, latitude, longitude, description = \
        payload['name'], payload['latitude'], \
        payload['longitude'], payload['description']
    async with request.app['db_pool'].acquire() as conn:
        await db.update_user(conn, name, latitude, longitude, description, user_id)
    return json_response(status=200)


async def delete_user(request: Request) -> Response:
    """ Delete a user by id. """
    try:
        user_id = int(request.match_info['user_id'])
    except ValueError:
        logger.error('Passed wrong user id: "%s", must be integer',
                     request.match_info['user_id'])
        raise HTTPBadRequest(text='User id must be integer')
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
