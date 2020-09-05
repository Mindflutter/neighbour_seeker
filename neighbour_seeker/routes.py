import logging
from pathlib import Path
from typing import Union

from aiohttp.web import Application, Request, Response, json_response, \
    HTTPNotFound
from aiohttp_swagger import setup_swagger

from neighbour_seeker import db
from neighbour_seeker.validators import user_schema, search_schema, \
    validate_user_id, validate_payload

logger = logging.getLogger(__name__)


async def get_user_row(request: Request, user_id: int) -> Union[Response, dict]:
    """ Get user DB row, raise 404 if not found. """
    async with request.app['db_pool'].acquire() as conn:
        user_row = await db.get_user(conn, user_id)
    if not user_row:
        logger.warning('User %s not found', user_id)
        raise HTTPNotFound(text='User not found')
    return user_row


@validate_user_id
async def get_user(request: Request) -> Response:
    """ Get user info by id. """
    user_id = int(request.match_info['user_id'])
    user_info = dict(await get_user_row(request, user_id))
    if not user_info['description']:
        user_info.pop('description')
    return json_response(data=user_info, status=200)


@validate_payload(user_schema)
async def create_user(request: Request) -> Response:
    """ Create a single user. """
    payload = await request.json()
    name, latitude, longitude, description = \
        payload['name'], payload['latitude'], \
        payload['longitude'], payload.get('description')
    async with request.app['db_pool'].acquire() as conn:
        user_id = await db.create_user(conn, name, latitude, longitude, description)
    response_data = {'user_id': user_id}
    return json_response(data=response_data, status=201)


@validate_user_id
@validate_payload(user_schema)
async def update_user(request: Request) -> Response:
    """ Update user information: name, description, coords. """
    user_id = int(request.match_info['user_id'])
    await get_user_row(request, user_id)
    payload = await request.json()
    name, latitude, longitude, description = \
        payload['name'], payload['latitude'], \
        payload['longitude'], payload.get('description')
    async with request.app['db_pool'].acquire() as conn:
        await db.update_user(conn, name, latitude, longitude, description, user_id)
    return json_response(status=200)


@validate_user_id
async def delete_user(request: Request) -> Response:
    """ Delete a user by id. """
    user_id = int(request.match_info['user_id'])
    await get_user_row(request, user_id)
    async with request.app['db_pool'].acquire() as conn:
        await db.delete_user(conn, user_id)
    return json_response(status=200)


@validate_payload(search_schema)
async def search(request: Request) -> Response:
    """ Perform KNN search returning nearest neighbour user ids. """
    payload = await request.json()
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

    openapi_path = Path(__file__).parent / 'resources' / 'openapi.yml'
    setup_swagger(app, swagger_url="/doc", ui_version=3,
                  swagger_from_file=openapi_path)
    logger.info('App routes initialized')
