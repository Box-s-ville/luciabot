from nonebot import get_bot, on_request
from nonebot.helpers import send_to_superusers
from nonebot.notice_request import RequestSession


__plugin_name__ = '处理请求 [Hidden]'


@on_request('friend', 'group.invite')
async def _(session: RequestSession):
    bot = session.bot
    event = session.event
    if event.detail_type == 'friend':
        msg = f'用户 {event.user_id} 请求添加好友。消息：{event.comment}'
    else:  # == 'group'
        msg = f'用户 {event.user_id} 邀请加入群 {event.group_id}。消息：{event.comment}'

    # 如果邀请者是超级用户，那么就自动同意请求
    if event.user_id in bot.config.SUPERUSERS:
        await session.approve()
        msg += '（已自动接受）'

    # 给超级用户发送这条消息
    await send_to_superusers(bot, msg)
    # TODO: 使用 broadcast() 广播这条消息到监控面板
