import asyncio
from nonebot import message_preprocessor
from nonebot.message import CQEvent
from nonebot.command import CommandSession
from nonebot.helpers import context_id
from nonebot.exceptions import CQHttpError
from nonebot.experimental.plugin import on_command

from services.command_use_count import record_successful_invocation
from services.broadcast import broadcast, listen_to_broadcasts


__plugin_name__ = 'grouptty'
__plugin_usage__ = (
    '用法：对我说 "grouptty" 查看当前的 tty 信息。\n'
    '对我说 "grouptty [群号]" 接入该群聊天。\n'
    '在此期间该群的聊天会被我转发到这里。\n'
    '你可以说 "grouptty.send [消息]" 来向此群发送消息。\n'
    '期间发送 "grouptty.end" 结束当前 tty。'
)


# 收到群聊消息时要广播一下
# 没错我们可以定义多个消息预处理器
@message_preprocessor
async def _(bot, event: CQEvent, manager):
    if not event.group_id:
        return

    async def _bc():
        return {
            'message': event.message,
            'user_id': event.user_id,
            'name': event.sender['card'] or event.sender['nickname'],
        }
                                  # 订阅的群组
    asyncio.create_task(broadcast(f'grouptty-{event.group_id}', _bc))


grouptty_permission = lambda sender: sender.is_superuser

# tty 发起者的 context（即 qq 号码 + 发起者群号（如果有）生成的唯一 ID） 值为相应的群号和从广播提取消息的循环
_ttys: dict[str, tuple[int, asyncio.Task]] = {}


@on_command('grouptty', permission=grouptty_permission)
@record_successful_invocation('grouptty')
async def _(session: CommandSession):
    # 如果用户已经有一个链接，就提示
    if (pair := _ttys.get(context_id(session.event))) is not None:
        await session.send(f'grouptty: 目前已经在监听群 {pair[0]}')
        return

    bot, event = session.bot, session.event
    group: str = session.current_arg_text.strip()
    # 如果用户不提供群号，就发送机器人所在的群列表
    if not group:
        available_groups = await bot.get_group_list()
        await session.send(
            'grouptty: 可以监听的群: ' +
            ', '.join(f"{g['group_id']}" for g in available_groups)
        )
        return

    async def _receive():
        # 订阅的群组
        with listen_to_broadcasts(f'grouptty-{group}') as get:
            while True:
                ev = (await get())['data']
                # 转发消息给当前会话
                await bot.send(event, f'grouptty: {ev["user_id"]} ({ev["name"]}): {ev["message"]}')

    _ttys[context_id(session.event)] = (int(group), asyncio.create_task(_receive()))
    await session.send('grouptty: 开始')


@on_command(('grouptty', 'end'), permission=grouptty_permission)
async def _(session: CommandSession):
    if (pair := _ttys.pop(context_id(session.event), None)) is not None:
        pair[1].cancel()
        await session.send('grouptty: 结束')
    else:
        await session.send('grouptty: 当前没有接入群聊！')


@on_command(('grouptty', 'send'), permission=grouptty_permission)
@record_successful_invocation('grouptty.send')
async def _(session: CommandSession):
    if (pair := _ttys.get(context_id(session.event))) is not None:
        msg = session.current_arg or await session.aget(prompt='grouptty>')
        try:
            await session.bot.send_group_msg(group_id=pair[0], message=msg)
        except CQHttpError:
            await session.send('grouptty: 发送失败！')
    else:
        await session.send('grouptty: 当前没有接入群聊！')
