from os import path

import nonebot
import bot_config
from services import db_context


nonebot.init(bot_config)
nonebot.load_plugins(path.join(path.dirname(__file__), 'bot_plugins'), 'bot_plugins')

nonebot.on_startup(db_context.init)

# 如果使用 asgi
bot = nonebot.get_bot()
app = bot.asgi

if __name__ == '__main__':
    nonebot.run()
