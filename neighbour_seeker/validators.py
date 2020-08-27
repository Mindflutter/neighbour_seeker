import logging
import traceback
from json.decoder import JSONDecodeError

from aiohttp.web import HTTPBadRequest
from jsonschema.exceptions import ValidationError

logger = logging.getLogger(__name__)

create_user_schema = \
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

update_user_schema = \
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
                "type": ["string", "null"],
                "maxLength": 256
            }
        },
        "required": [
            "name",
            "latitude",
            "longitude",
            "description"
        ]
    }

search_schema = {
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
            "exclusiveMinimum": 0,
        },
    },
    "required": [
        "user_id",
        "count",
        "distance"
    ]
}


def validate_json(func):
    """ A decorator for handling various JSON errors. """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as error:
            # return short description, log full error
            logger.error('JSON Validation error: %s', error)
            raise HTTPBadRequest(text=f'Error: {error.message}')
        except JSONDecodeError as error:
            logger.error('JSON Decode error: %s', traceback.format_exc())
            raise HTTPBadRequest(text=f'JSON Decode error: {error}')

    return wrapper


def validate_user_id(input_user_id):
    """ Simple integer validator, raises 400 if not ok. """
    try:
        return int(input_user_id)
    except ValueError:
        logger.error('Passed wrong user id: "%s", must be integer',
                     input_user_id)
        raise HTTPBadRequest(text='User id must be integer')
