from gino import Gino

from service_config import DATABASE_URI
from .log import logger


# 全局数据库连接对象
db = Gino()


async def init():
    'Initialise psql database connection. Program must exit before the connection is freed.'
    await db.set_bind(DATABASE_URI)
    await db.gino.create_all()

    logger.info(f'Database loaded successfully!')
