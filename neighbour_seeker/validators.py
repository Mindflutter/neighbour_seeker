import logging
import traceback
from json.decoder import JSONDecodeError

import jsonschema
from aiohttp.web import HTTPBadRequest
from jsonschema.exceptions import ValidationError

logger = logging.getLogger(__name__)

user_schema = \
    {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "maxLength": 64
            },
            "latitude": {
                "type": "number",
                "minimum": -90,
                "maximum": 90
            },
            "longitude": {
                "type": "number",
                "minimum": -180,
                "maximum": 180
            },
            "description": {
                "type": "string",
                "maxLength": 256
            }
        },
        "required": [
            "name",
            "latitude",
            "longitude"
        ]
    }

search_schema = \
    {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "minimum": 1
            },
            "count": {
                "type": "integer",
                "minimum": 1
            },
            "distance": {
                "type": "number",
                "exclusiveMinimum": 0
            }
        },
        "required": [
            "user_id",
            "count",
            "distance"
        ]
    }


def validate_payload(schema: dict):
    """ Validate payload according to the provided schema. """

    def validate_json(func):
        """ A decorator for handling various JSON errors. """

        async def wrapper(*args):
            request = args[0]
            try:
                payload = await request.json()
                jsonschema.validate(payload, schema)
                return await func(*args)
            # return short description, log full error
            except ValidationError as error:
                logger.error('JSON Validation error: %s', error)
                raise HTTPBadRequest(text=f'Error: {error.message}')
            except JSONDecodeError as error:
                logger.error('JSON Decode error: %s', traceback.format_exc())
                raise HTTPBadRequest(text=f'JSON Decode error: {error}')

        return wrapper

    return validate_json


def validate_user_id(func):
    """ Simple integer validator, raises 400 if not ok. """

    async def wrapper(*args):
        request = args[0]
        input_user_id = request.match_info['user_id']
        try:
            int(input_user_id)
            return await func(*args)
        except ValueError:
            logger.error('Passed wrong user id: "%s", must be integer',
                         input_user_id)
            raise HTTPBadRequest(text='User id must be integer')

    return wrapper
