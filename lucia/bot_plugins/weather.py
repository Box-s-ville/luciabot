from nonebot.command import CommandSession
from nonebot.natural_language import NLPSession, IntentCommand
from nonebot.experimental.plugin import on_command, on_natural_language
from jieba import posseg

from services.common import ServiceException
from services.weather import get_current_weather_short, get_current_weather_desc


__plugin_name__ = '天气'
__plugin_usage__ = (
    '用法：\n'
    '对我说 “天气 香港” 获取天气简要\n'
    '“天气 香港 详细” 获取当前天气的详细报告'
)


# 表示 “不是私聊” 或 “超级用户” 可以触发此命令
weather_permission = lambda sender: (not sender.is_privatechat) or sender.is_superuser


@on_command('weather', aliases=('气温', '天气'), permission=weather_permission)
async def _(session: CommandSession):
    # 尝试从用户提供的信息中提取参数，如果没有参数，则主动询问
    # 若用户对机器人说“天气”，则此变量为 `['']`
    # 若用户对机器人说“天气 香港”，则此变量为 `['香港']`
    # 若用户对机器人说“天气 香港 详细”，则此变量为 `['香港', '详细']`
    args = session.current_arg_text.strip().split(' ', 1)

    if not args[0]:
        city = await session.aget(key='city', prompt='请问是什么城市呢？', at_sender=True)
    else:
        city = args[0]

    is_detailed = (len(args) == 2 and args[1] == '详细') or session.state.get('is_detailed')

    # 在这里调用 weather service，获取结果
    try:
        func = get_current_weather_desc if is_detailed else get_current_weather_short
        result = await func(city)
    except ServiceException as e:
        result = e.message

    # 将结果原封不动发送给用户
    await session.send(result)


# 只要消息包含“天气”，就执行此处理器
@on_natural_language(keywords={'天气'}, permission=weather_permission)
async def _(session: NLPSession):
    # 使用 jieba 将消息句子分词
    words = posseg.lcut(session.msg_text.strip())

    args = {}

    for word in words:
        if word.flag == 'ns': # ns 表示该词为地名
            args['city'] = word.word
        elif word.word in ('详细', '报告', '详情'):
            args['is_detailed'] = True

    # 置信度为 90，意为将此会话当作 'weather' 命令处理
    return IntentCommand(90, 'weather', args=args)
