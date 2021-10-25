# 使用 NoneBot 和 go-cqhttp 搭建 QQ 群聊机器人

## 完善配置项

如果我们不想总使用斜杠来与机器人交谈，可以在设置文件中设置她的命令前缀（`COMMAND_START`）变量，同时还可以在此给机器人起一些昵称。

打开 `lucia/bot_config.py`，添加或替换成如下内容：

```py
# ... 略

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
from nonebot.plugin import on_command

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
在此之前我们先再给天气插件提供一个功能。打开先前的 `luciabot/lucia/services/weather.py`，文件，在底下添加以下方法：
```py
@cached(ttl=60)
async def get_current_weather_desc(city: str) -> str:
    _format = (
        '%l:\n'
        '+%c+%C:+%t\n'
        '+💦+Humidity:+%h\n'
        '+💧+Precipitation:+%p\n'
        '+🍃+Wind:+%w'
    )
    return await fetch_text(f'https://wttr.in/{city}?format={_format}')
```
这个方法返回一个更为详细的天气报告。`_format` 是传递给 wttr api 的格式化字符串，你可以在其项目地址中找到详细介绍。

然后我们来让这个变动反映在天气插件中，仍然打开 `luciabot/lucia/bot_plugins/weather.py`，将命令处理器替换成如下：
```py
# ... 略
from services.weather import get_current_weather_short, get_current_weather_desc


__plugin_name__ = '天气'
__plugin_usage__ = (
    '用法：\n'
    '对我说 “天气 香港” 获取天气简要\n'
    '“天气 香港 详细” 获取当前天气的详细报告'
)


weather_permission = lambda sender: (not sender.is_privatechat) or sender.is_superuser


@on_command('weather', aliases=('气温', '天气'), permission=weather_permission)
async def _(session: CommandSession):
    # 若用户对机器人说“天气”，则此变量为 `['']`
    # 若用户对机器人说“天气 香港”，则此变量为 `['香港']`
    # 若用户对机器人说“天气 香港 详细”，则此变量为 `['香港', '详细']`
    args = session.current_arg_text.strip().split(' ', 1)

    if not args[0]:
        city = await session.aget(key='city', prompt='请问是什么城市呢？', at_sender=True)
    else:
        city = args[0]

    is_detailed = (len(args) == 2 and args[1] == '详细') or session.state.get('is_detailed')

    try:
        func = get_current_weather_desc if is_detailed else get_current_weather_short
        result = await func(city)
    except ServiceException as e:
        result = e.message

    await session.send(result)
```

Tip: 实际应用中需要验证参数是不是一个合法的城市名，否则 wttr 会返回搞笑的结果。在这里为了方便略过了。

在这里（`aget` 的 `key`，和 `is_detailed` 的判定）我们引入了 `session` 的 `state`。这个变量可以帮助我们访问或修改当前会话中的状态，例如在 `session.aget()` 中，我们会先在会话状态中寻找 `city` 字段，如果存在，则此函数直接返回相应值，否则就将会询问用户，再把用户的反应存放入状态中返回。

这个特性目前我们还用不到。

我们来看实际运行时的例子：
```
群主:
  莉西亚 天气
lucia:
  @群主  请问是什么城市呢？
群主:
  东京
lucia:
  ⛅️ +21°C
群主:
  莉西亚 天气 东京
lucia:
  ⛅️ +21°C
群主:
  莉西亚 天气 东京 详细
lucia:
  东京:
   ⛅️ Partly cloudy: +17°C
   💦 Humidity: 41%
   💧 Precipitation: 0.0mm
   🍃 Wind: ↓8km/h
```

我们想每次都要使用这种近似于命令行的交互方式吗？使用空格分割字符串很方便，但是使用者会觉得很奇怪。对于这种包括参数交互的命令，可以使用自然语言处理器来强化它。

在本例子里使用一个中文分词库 - [jieba](https://github.com/fxsjy/jieba)。使用此库可以比较方便地从长句子中提取需要的词汇。
```sh
$ pip install jieba
```

回到天气插件的文件，添加以下内容：
```py
# ... 略
from nonebot.natural_language import NLPSession, IntentCommand
from nonebot.plugin import on_command, on_natural_language
from jieba import posseg

# ... 略

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
```

在这里我们解析用户提供的句子并且手工构造一个相应的初始会话状态（参数），最后以 `IntentCommand` 的方式传递给 NoneBot 的命令管理器。一个句子可以被多个自然语言处理器处理，每一个处理器都返回相应的 `IntentCommand`，置信度会决定哪一个命令会被最终调用。

再来看一下使用的例子：
```
群主:
  莉西亚，现在天气怎么样
lucia:
  @群主  请问是什么城市呢？
群主:
  京都
lucia:
  ⛅️ +21°C
群主:
  莉西亚，京都天气怎么样
lucia:
  ⛅️ +21°C
群主:
  莉西亚，京都详细天气
lucia:
  京都:
   ⛅️ Partly cloudy: +21°C
   💦 Humidity: 60%
   💧 Precipitation: 0.0mm
   🍃 Wind: ↑9km/h
```

Tip: 过度使用自然语言处理可能会拖慢机器人响应速度，使用时需权衡。
