import logging.config

from aiohttp import web
from aiohttp_swagger import setup_swagger

from neighbour_seeker import config
from neighbour_seeker.db import init_db, close_db
from neighbour_seeker.routes import setup_routes


def main():
    """ Application entry point. """
    logging.config.dictConfig(config.LOGGING_CONFIG)
    app = web.Application()
    setup_routes(app)
    app.on_startup.append(init_db)
    app.on_cleanup.append(close_db)
    setup_swagger(app, swagger_url="/doc", ui_version=3, swagger_from_file='openapi.yaml')
    web.run_app(app)


if __name__ == '__main__':
    main()
