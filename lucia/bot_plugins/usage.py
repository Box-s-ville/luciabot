from nonebot import get_loaded_plugins
from nonebot.command import CommandSession
from nonebot.experimental.plugin import on_command

from services.command_use_count import record_successful_invocation


__plugin_name__ = '帮助'
__plugin_usage__ = (
    '用法：\n'
    '对我说 “帮助” 获取我支持的功能\n'
    '“帮助 功能名” 获取对应详细帮助'
)


help_permission = lambda sender: (not sender.is_privatechat) or sender.is_superuser


@on_command('help', aliases={'帮助'}, permission=help_permission)
@record_successful_invocation('help')
async def _(session: CommandSession):
    # 获取加载的插件，注意名字以 [Hidden] 结尾的不应该被展示！
    plugins = (p for p in get_loaded_plugins() if p.name and not p.name.endswith('[Hidden]'))

    arg = session.current_arg_text.strip()
    # 没有参数：展示功能列表
    if not arg:
        await session.send(
            '我的功能有：\n  ' + '\n  '.join(p.name for p in plugins) +
            '\n对我说 “帮助 功能名” 获取对应详细帮助'
        )
    # 有参数：展示对应 usage
    else:
        for p in plugins:
            if arg.lower() in p.name.lower():
                await session.send(p.usage)
