import os

from gino import Gino

from .log import logger


# 全局数据库连接对象
db = Gino()


async def init():
    'Initialise psql database connection. Program must exit before the connection is freed.'
    uri = os.environ['DATABASE_URI']
    await db.set_bind(uri)
    await db.gino.create_all()

    logger.info(f'Database loaded successfully!')
