# 使用 NoneBot 和 go-cqhttp 搭建 QQ 群聊机器人

## 处理请求

NoneBot 也提供了 `on_request` 和 `on_notice` 装饰器。当机器人收到请求的时候便会调用相应的处理器，例如下面的例子。

创建 `luciabot/lucia/bot_plugins/request_handler.py`：
```py
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
```

这个处理器会处理好友请求和邀请机器人加群的请求。[OneBot](https://github.com/howmanybots/onebot/blob/master/v11/specs/event/request.md) 中规定了相关的请求种类。

当机器人收到请求的时候，调用辅助函数 `send_to_superusers` 将 `msg` 私聊给所有的超级用户。例子：
```
lucia:
  用户 123456789 请求添加好友。消息：一些验证消息（已自动接受）
```

## 为机器人编写说明书
最后，我们的机器人既然已经有了 4 个功能，那么组织一份“帮助”命令显得很重要。

得利于我们为每个插件都之前定义过 `__plugin_name__` 和 `__plugin_usage__` 常量，我们可以利用它们来生成一份帮助信息。来看下面的例子：

`luciabot/lucia/bot_plugins/usage.py`
```py
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
```

本例中为了方便返回了一份非常 generic 的帮助信息。用户也可以根据自己的需求从 `get_loaded_plugins` api 中筛选想要的插件。

我们来尝试调用一下这个功能：
```
群主:
  莉西亚，帮助
lucia:
  我的功能有：
    ping
    grouptty
    帮助
    天气
    签到
  对我说 “帮助 功能名” 获取对应详细帮助
群主:
  莉西亚，帮助 帮助
lucia:
  用法：
  对我说 "帮助" 获取我支持的功能
  “帮助 功能名” 获取对应详细帮助
群主:
  莉西亚，帮助 ping
lucia:
  用法： 对我说 "ping"，我会回复 "pong!"
群主:
  莉西亚，ping
lucia:
  pong!
```

好吧，现在是 5 个功能。

## 下一步
我们的机器人已经近乎完备，这里对 NoneBot 的介绍也差不多要结束了。从此以后，我们就可以像搭积木一样向这个框架添加功能。

这个机器人的提升空间有：
* 我们要补充 service 中的异常处理
* 提取一些公共函数，比如 `ensure`
* 分离生产和开发用的环境
* 提供更完善的面板，比如展示好友请求
* 等等...
* 更多的功能！

此教程对 NoneBot api 的介绍不是 100% 全面，仍有很多没有被提及的地方。读者可以查看官方文档来取得更多的样例融入到自己的项目中。

* NoneBot 框架: https://docs.nonebot.dev/
* OneBot 标准: https://github.com/howmanybots/onebot
* nb2 框架: https://github.com/nonebot/nonebot2
* gocqhttp: https://github.com/Mrs4s/go-cqhttp

不要忘了 NoneBot 支持主动调用 gocqhttp 的 api！例如
```py
bot = get_bot()
await bot.set_group_kick(group_id=87654321, user_id=9876543210)
```
可以将用户踢出群聊。

-------------------------------------------------------------

这是最终 lucia 的目录结构：
```
lucia
├── Dockerfile
├── bot.py
├── bot_config.py
├── bot_plugins/
│   ├── group_user_checkin.py
│   ├── grouptty.py
│   ├── inmsg_count.py
│   ├── ping.py
│   ├── request_handler.py
│   ├── usage.py
│   └── weather.py
├── controllers.py
├── models/
│   ├── command_use.py
│   └── group_user.py
├── requirements.txt
├── resources/
│   ├── SourceHanSans-Regular.otf
│   ├── dashboard.html
│   └── group_user_check_bg.png
├── service_config.py
└── services/
    ├── broadcast.py
    ├── command_use_count.py
    ├── common.py
    ├── db_context.py
    ├── group_user_checkin.py
    ├── inmsg_count.py
    ├── log.py
    ├── processpool.py
    └── weather.py
```

Cheers!

![img](../lucia/resources/group_user_check_bg.png)
