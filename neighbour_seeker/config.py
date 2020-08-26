import os

# using connection string for convenience, could be separate config values
PG_DSN = os.getenv('PG_DSN', default='postgres://geo:secret@localhost:5432/geodb')
PG_POOL_SIZE = int(os.getenv('PG_POOL_SIZE', default=10))

LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', default='INFO')
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'app': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': LOGGING_LEVEL,
            'formatter': 'app',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': LOGGING_LEVEL,
            'propagate': False
        },
        # silence framework messages down to warning level
        'aiohttp': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False
        }
    }
}
