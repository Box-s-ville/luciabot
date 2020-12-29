from nonebot.command import CommandSession
from nonebot.experimental.plugin import on_command

from services.command_use_count import record_successful_invocation


__plugin_name__ = 'ping'
__plugin_usage__ = '用法： 对我说 "ping"，我会回复 "pong!"'


@on_command('ping', permission=lambda sender: sender.is_superuser)
@record_successful_invocation('ping')  # 命令名 - 或者是任何表示名字的字符串
async def _(session: CommandSession):
    await session.send('pong!')
