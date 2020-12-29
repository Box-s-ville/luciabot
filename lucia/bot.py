from os import path

import nonebot
import bot_config
from controllers import add_controllers
from services import db_context, inmsg_count


nonebot.init(bot_config)
nonebot.load_plugins(path.join(path.dirname(__file__), 'bot_plugins'), 'bot_plugins')

nonebot.on_startup(db_context.init)
nonebot.on_startup(inmsg_count.init)

# 如果使用 asgi
bot = nonebot.get_bot()
app = bot.asgi

add_controllers(bot.server_app)

if __name__ == '__main__':
    nonebot.run()
