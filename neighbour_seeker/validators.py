import logging
import traceback
from json.decoder import JSONDecodeError

from aiohttp import web
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
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as error:
            # return short description, log full error
            logger.error('JSON Validation error: %s', error)
            raise web.HTTPBadRequest(text=f'Error: {error.message}')
        except JSONDecodeError as error:
            logger.error('JSON Decode error: %s', traceback.format_exc())
            raise web.HTTPBadRequest(text=f'JSON Decode error: {error}')
    return wrapper
