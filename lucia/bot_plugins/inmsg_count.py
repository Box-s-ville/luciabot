from nonebot import message_preprocessor

from services import inmsg_count


__plugin_name__ = '消息计数 [Hidden]'


@message_preprocessor
async def _(bot, event, manager):
    await inmsg_count.increase_now()
