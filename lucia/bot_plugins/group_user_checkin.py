from nonebot import get_bot
from nonebot.command import CommandSession
from nonebot.experimental.plugin import on_command
from aiocqhttp.message import MessageSegment

from services.group_user_checkin import group_user_check_in, group_user_check, group_user_check_use_b64img
from services.command_use_count import record_successful_invocation


__plugin_name__ = '签到'
__plugin_usage__ = (
    '用法：\n'
    '对我说 “签到” 来签到\n'
    '“我的签到” 或 “我的签到 文本” 来获取历史签到信息'
)


# 此功能只在群聊有效
checkin_permission = lambda sender: sender.is_groupchat


@on_command('签到', permission=checkin_permission)
@record_successful_invocation('签到')
async def _(session: CommandSession):
    await session.send(
        await group_user_check_in(session.event.user_id, session.event.group_id), # type: ignore
        at_sender=True,
    )


@on_command('我的签到', aliases={'好感度'}, permission=checkin_permission)
@record_successful_invocation('我的签到')
async def _(session: CommandSession):
    user_id, group_id = session.event.user_id, session.event.group_id
    if session.current_arg and session.current_arg.strip() == '文本':
        await session.send(await group_user_check(user_id, group_id), at_sender=True)
    else:
        # 使用 bot 对象来主动调用 api
        nickname = (await get_bot().get_stranger_info(user_id=user_id))['nickname'] # type: ignore
        im_b64 = await group_user_check_use_b64img(user_id, group_id, nickname)
        await session.send(MessageSegment.image(f'base64://{im_b64}'), at_sender=True)

