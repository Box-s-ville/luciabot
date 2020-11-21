from nonebot.command import CommandSession
from nonebot.experimental.plugin import on_command

from services.group_user_signin import group_user_sign_in, group_user_check


__plugin_name__ = '签到'
__plugin_usage__ = (
    '用法：\n'
    '对我说 “签到” 来签到\n'
    '“我的签到” 来获取历史签到信息'
)


# 此功能只在群聊有效
signin_permission = lambda sender: sender.is_groupchat


@on_command('签到', permission=signin_permission)
async def _(session: CommandSession):
    await session.send(
        await group_user_sign_in(session.event.user_id, session.event.group_id), # type: ignore
        at_sender=True,
    )


@on_command('我的签到', aliases={'好感度'}, permission=signin_permission)
async def _(session: CommandSession):
    await session.send(
        await group_user_check(session.event.user_id, session.event.group_id), # type: ignore
        at_sender=True,
    )
