from nonebot.command import CommandSession
from nonebot.experimental.plugin import on_command

from services.common import ServiceException
from services.weather import get_current_weather_short


__plugin_name__ = '天气'
__plugin_usage__ = '用法： 对我说 “天气 香港”'


# 表示 “不是私聊” 或 “超级用户” 可以触发此命令
@on_command('weather', aliases=('气温', '天气'), permission=lambda sender: (not sender.is_privatechat) or sender.is_superuser)
async def _(session: CommandSession):
    # 尝试从用户提供的信息中提取参数，如果没有参数，则主动询问
    city = session.current_arg_text.strip()
    if not city:
        city = await session.aget(prompt='请问是什么城市呢？', at_sender=True)

    # 在这里调用 weather service，获取结果
    try:
        result = await get_current_weather_short(city)
    except ServiceException as e:
        result = e.message

    # 将结果原封不动发送给用户
    await session.send(result)
