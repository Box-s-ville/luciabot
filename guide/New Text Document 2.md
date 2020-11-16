# 使用 NoneBot 和 go-cqhttp 搭建 QQ 群聊机器人

## 完善配置项

如果我们不想总使用斜杠来与机器人交谈，可以在设置文件中设置她的命令前缀（`COMMAND_START`）变量，同时还可以在此给机器人起一些昵称。

打开 `lucia/bot_config.py`，添加或替换成如下内容：

```py
# 我们不使用命令前缀
COMMAND_START = { '' }
# 机器人昵称，设定后 "@机器人 天气" 和 "lucia 天气" 效果相同。
NICKNAME = { 'lucia', 'Lucia', '莉西亚' }
# 关闭调试输出，提升性能。
DEBUG = False
```

[官方文档](https://docs.nonebot.dev/api.html#%E9%85%8D%E7%BD%AE) 中讲述了更多配置选项，在这篇文章里只使用了部分。

此时在群聊中我们就可以发送：
```
群主:
  莉西亚，ping
lucia:
  pong!
```
而不用特地去艾特机器人或者是加入斜杠了。

同理在私聊中，我们也不需要加斜杠了。

Tip: 在处理命令时，机器人会先决定发送者 “是否在于它” 对话，以下情境中会被视为发送者在与机器人对话：
* 和机器人私聊
* 在群聊中 @机器人
* 发送的消息包括机器人的昵称作为开头

只有在被视为与机器人对话时，才会开始响应的命令处理。

## 编写实用插件
我们从最简单的天气插件开始。因为要获取天气，我们要请求 API，所以需要合适的库来提我们做 HTTP 请求。在开始之前，先引入如下 pip 包：
```
$ pip install httpx aiocache
```
NoneBot 是基于 async/await 风格的机器人框架，所以也最好使用相同风格的 IO 库。在这里 httpx 是相当于 requests 的网络库，aiocache 提供缓存功能。NoneBot 应该已经自带这些库作为依赖，你可以选择仍然运行这些命令来获取它们的最新版本。

天气服务这里选择一个命令行 API wttr.in，使用它可以很简单地获取基于文字和 emoji 的天气简介。你可以现在命令行中试验一下：
```sh
$ curl 'wttr.in/HongKong?format=1'
🌦 +22°
```

当然，在实际的项目中，最好使用一个标准的 API。

这篇文章里使用类似 MVCS 的结构，首先在 `lucia` 文件夹中建立 `services` 文件夹，添加如下文件：

`luciabot/lucia/services/common.py`
```py
from httpx import AsyncClient, HTTPError

from .log import logger


class ServiceException(Exception):
    'Base of exceptions thrown by the service side'
    def __init__(self, message: str) -> None:
        super().__init__(message)

    @property
    def message(self) -> str:
        return self.args[0]


async def fetch_text(uri: str) -> str:
    async with AsyncClient(headers={ 'User-Agent': 'box-s-ville.luciabot' }) as client:
        try:
            res = await client.get(uri)
            res.raise_for_status()
        except HTTPError as e:
            logger.exception(e)
            raise ServiceException('API 服务目前不可用')
        return res.text
```

这个文件定义一个服务模块的异常类型和一个用于 HTTP GET TEXT 文件的辅助函数。

`luciabot/lucia/services/log.py`
```py
import logging
import sys


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(
    logging.Formatter('[%(asctime)s %(name)s] %(levelname)s: %(message)s')
)

logger = logging.getLogger('lucia')
logger.addHandler(_handler)
logger.setLevel(logging.INFO)
```

这个文件提供一个 logging 服务，其输出模式和 NoneBot 内置的 logging 一致。当我们自己的代码想要打印东西时，可以使用这个服务。使用分别的 logging 可以帮助区分问题是在于我们自己的机器人还是 NoneBot 框架本身。

Tip: `logger.setLevel()` 如有必要，可以设置其从配置文件读取，例如 `bot_config.py`。

接下来实现真正的天气服务：

`luciabot/lucia/services/weather.py`
```py
from aiocache import cached

from .common import fetch_text


@cached(ttl=60) # 结果缓存 60 秒
async def get_current_weather_short(city: str) -> str:
    return (await fetch_text(f'https://wttr.in/{city}?format=1')).strip()
```
可以看到我们在这里直接获取 API 的文字数据，正如刚才和终端中的一样。

为了使用这个刚定义的服务，我们也来像之前的 ping 插件一样，也来写一个命令插件。新建文件 `luciabot/lucia/bot_plugins/weather.py` 加入如下内容：
```py
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
```

最上面的几行是通用的模板代码。我们来看 `on_command`，这里多了一些东西。

在这里，`weather` 仍然表示命令的名称，在用户对机器人输入 `weather` 后会触发该处理器。`aliases` 中的内容表示的是别名，用户输入这些别名之一也可以触发此命令。

最后的 `permission` 参数表示命令的权限，例子中的参数表示 “不是私聊” 或 “超级用户” 可以触发此命令，这代表
* 超级用户私聊机器人可以触发此命令
* 超级用户在群聊中喊机器人的昵称可以触发此命令
* 普通群员在群聊中喊机器人的昵称可以触发此命令
* 讨论组中喊机器人的昵称可以触发此命令
* 普通用户私聊机器人不能触发此命令

而这一切都是可以自定义的，更多关于权限控制的内容可以在文档中查看。

Tip: 如果你直接从 `nonebot` 导入了 `on_command`，则效果相同的 `permission` 参数为 `GROUP_MEMBER | DISCUSS | SUPERUSER`。

`CommandSession` 中包含了当前会话的状态，也包括用户是否发送了其余的参数（即跟随在命令名 "weather" 或其别名后的任何文字内容）。在这个例子里，如果用户提供了参数（即城市名），那么直接从其中提取城市名字，否则我们将会询问发送者。来看如下例子。

运行机器人，切换到群聊窗口，尝试与机器人互动：
```
群主:
  莉西亚，weather 香港
lucia:
  🌦 +22°C
群主：
  莉西亚，天气
lucia:
  @群主  请问是什么城市呢？
群主：
  澳门
lucia:
  ⛅️ +23°C
```

与机器人私聊也可以，此时可以不包括机器人的昵称。

此时你的 NoneBot 工作目录应该形如：
```
lucia
├── bot.py
├── bot_config.py
├── bot_plugins/
│   ├── ping.py
│   └── weather.py
└── services/
    ├── common.py
    ├── log.py
    └── weather.py
```

恭喜，你已经完成了第一个具有实用功能的插件！

## 使用自然语言处理器完善天气插件

