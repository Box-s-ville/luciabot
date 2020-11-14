from nonebot.default_config import *

from datetime import timedelta


# 表示“超级用户”，也就是机器人的主人。超级用户拥有最高的权限。在这里填入你的 QQ 号。
SUPERUSERS = { 123456789 }

# 表示命令的前缀，例如假如命令叫 `天气`，那么只有用户在输入 `/天气` 时候才会触发命令。
COMMAND_START = { '/' }

# 表示一条命令的最长处理时间。
SESSION_EXPIRE_TIMEOUT = timedelta(minutes=2)

# 服务器和端口
HOST = '127.0.0.1'
PORT = 8765
