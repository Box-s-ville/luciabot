# 使用 NoneBot 和 go-cqhttp 搭建 QQ 群聊机器人

原先 [NoneBot](https://github.com/nonebot/nonebot) 的文档过于老旧，有些内容可能没有参考价值。例如官方 README 中节选：
> NoneBot 是一个基于 酷Q 的 Python 异步 QQ 机器人框架，它会对 QQ 机器人收到的消息进行解析和处理，并以插件化的形式，分发给消息所对应的命令处理器和自然语言处理器，来完成具体的功能。
>
> 除了起到解析消息的作用，NoneBot 还为插件提供了大量实用的预设操作和权限控制机制，尤其对于命令处理器，它更是提供了完善且易用的会话机制和内部调用机制，以分别适应命令的连续交互和插件内部功能复用等需求。

这里的 酷Q 早就在八月就凉了。新手看到后可能会觉得一头雾水。于是本文的目的即是演示从零搭建一个 QQ 机器人，读完后或许可以消除新人的疑惑。

## 可以不看
NoneBot 过去是基于 酷Q 和 CQHttp 插件的机器人框架。可以理解为 酷Q 和 CQhttp 为机器人的“后端”，用于处理通信和协议，而 NoneBot 为 “前端”，负责机器人的逻辑，如发送天气等。随着八月初各大“后端”框架的扑街，两者一度被废弃至今。

不过在这之后出现了 [OneBot](https://github.com/howmanybots/onebot) “标准”，提供和 CQHttp 类似的 api 规则。很多现在的机器人“后端”都可以遵循此标准，例如 go-cqhttp 和 mirai native 等。所以选择对的后端对实际上开发没有太大的影响。比如 go-cqhttp，可以当作 酷Q 的"drop-in replacement"。

## 开始使用 Nonebot
首先使用 pip 安装 nonebot （截至此稿完成最新版本为 1.8.0）：
```sh
$ pip install nonebot
```

我的机器人的名字叫 `lucia`。创建项目文件夹 `luciabot`，并且添加如下文件夹和空文件：
```
luciabot/
└── lucia/
    ├── bot.py
    ├── bot_config.py
    └── bot_plugins/
        └── ping.py
```

我们来逐个解释这三个文件。

打开 `lucia/bot_config.py`，添加以下内容：
```py
from nonebot.default_config import *

from datetime import timedelta


# 表示“超级用户”，也就是机器人的主人。超级用户拥有最高的权限。在这里填入你的 QQ 号。
SUPERUSERS = { 123456789 }
# 表示命令的前缀，例如假如命令叫 `天气`，那么只有用户在输入 `/天气` 时候才会触发命令。
COMMAND_START = { '/' }
# 表示一条命令的最长处理时间。
SESSION_EXPIRE_TIMEOUT = timedelta(minutes=2)
# 服务器和端口
HOST = '127.0.0.1'
PORT = 8765
```

这是我们的配置文件。第一行的 `import` 表示先导入 nonebot 自带的配置，而后我们再在这个文件里覆盖我们想自定义的项目。

最后两行表示机器人运行的地址和端口。由于 nonebot 基于 [Quart](https://pgjones.gitlab.io/quart/index.html)，其会开启一个 Web 服务器，并以此和 onebot 后端沟通。

打开 `lucia/bot.py`，添加以下内容：
```py
from os import path

import nonebot
import bot_config


nonebot.init(bot_config)
# 第一个参数为插件路径，第二个参数为自定义插件前缀
nonebot.load_plugins(path.join(path.dirname(__file__), 'bot_plugins'), 'bot_plugins')

# 如果使用 asgi
bot = nonebot.get_bot()
app = bot.asgi

if __name__ == '__main__':
    nonebot.run()
```

首先我们导入 `bot_config.py` 并将其传入初始化函数中，再加载所有位于 `lucia/bot_plugin` 目录下的插件，最后调用 `nonebot.run()` 来启动程序。

## 编写 NoneBot 插件
以上的启动文件会设置为加载 `lucia/bot_plugin` 下的所有插件。一个插件的定义如下：可以是一个 `.py` 文件，或者可以是一个文件夹，其中包含 `__init__.py` 入口文件。我们第一个插件选择的是前者的简单方式。打开先前创建的 `luciabot/lucia/bot_plugins/ping.py` 文件，添加如下代码：
```python
from nonebot.command import CommandSession
from nonebot.experimental.plugin import on_command


__plugin_name__ = 'ping'
__plugin_usage__ = '用法： 对我说 "ping"，我会回复 "pong!"'


@on_command('ping', permission=lambda sender: sender.is_superuser)
async def _(session: CommandSession):
    await session.send('pong!')
```

一个插件最好能够定义其插件名和介绍，正如 `__plugin_name__` 和 `__plugin_usage__` 一样。

`on_command` 装饰器会将一个函数注册为命令处理器，其中第一个参数为命令的名字，在这里我还设置了此命令的权限：`lambda sender: sender.is_superuser` 表示只有超级用户（也就是你）才能够触发这条命令，机器人会无视其余用户。

当命令被触发时，nonebot 会创建一个 `CommandSession` 对象用来代表当前的会话。在这里我们向发送者发送回一条信息。

这就是最小的 nonebot 机器人实例，你现在可以使用 `python bot.py` 命令来运行此程序，不过仅靠这还不行，因为我们现在还没有后端。

## 用 go-cqhttp 替代 CQHttp
在 `luciabot` 下创建 `gocqhttp` 文件夹，到其 [release](https://github.com/Mrs4s/go-cqhttp/releases) 页面里下载适合自己平台的可执行文件并且解压到到此文件夹中（目前版本为 v0.9.30，若因版本更新导致配置文件格式变化，请参照与其默认配置不同处）。在相同的目录下创建 go-cqhttp 的配置文件，如下：

`luciabot/gocqhttp/config.json`:
```json
{
  "uin": 11111111,
  "password": "123456",
  "encrypt_password": false,
  "password_encrypted": "",
  "enable_db": true,
  "access_token": "",
  "relogin": {
    "enabled": true,
    "relogin_delay": 3,
    "max_relogin_times": 0
  },
  "_rate_limit": {
    "enabled": false,
    "frequency": 1,
    "bucket_size": 1
  },
  "ignore_invalid_cqcode": false,
  "force_fragmented": false,
  "heartbeat_interval": 10,
  "http_config": {
    "enabled": false,
    "host": "0.0.0.0",
    "port": 5700,
    "timeout": 0,
    "post_urls": {}
  },
  "ws_config": {
    "enabled": false,
    "host": "0.0.0.0",
    "port": 6700
  },
  "ws_reverse_servers": [
    {
      "enabled": true,
      "reverse_url": "ws://127.0.0.1:8765/ws",
      "reverse_api_url": "",
      "reverse_event_url": "",
      "reverse_reconnect_interval": 3000
    }
  ],
  "post_message_format": "string",
  "debug": false,
  "log_level": "",
  "web_ui": {
    "enabled": false,
    "host": "0.0.0.0",
    "web_ui_port": 9999,
    "web_input": false
  }
}
```
在这里前两个配置（`"uin"`, `"password"`）是机器人登录 QQ 号和密码。

由于 nonebot 只通过开启 websocket 服务器来和后端沟通，所以在这里的配置文件中我们关闭 http 和正向 ws，只保留反向 ws （即 `"ws_reverse_servers"`）。请保证 `"reverse_url"` 的配置与 `luciabot/lucia/bot_config.py` 中的 IP 和端口一致。

这一步完成后，项目目录应如图所示：

```
luciabot/
├── gocqhttp/       
│   ├── config.json
│   └── go-cqhttp
└── lucia/        
    ├── bot.py
    ├── bot_config.py
    └── bot_plugins/
        └── ping.py
```

现在我们两者都已经准备好了，现在就到了最激动人心的环节 - 实际运行我们的 bot。

执行 NoneBot：
```sh
$ cd lucia && python bot.py

ujson module not found, using json
msgpack not installed, MsgPackSerializer unavailable
[2020-11-11 02:47:36,123 nonebot] INFO: Succeeded to import "bot_plugins.ping"
[2020-11-11 02:47:36,124 nonebot] INFO: Running on 127.0.0.1:8765
Running on http://127.0.0.1:8765 (CTRL + C to quit)
[2020-11-11 02:47:36,209] Running on http://127.0.0.1:8765 (CTRL + C to quit)
```

在这里可以看到我们的 `ping` 插件成功加载了。

运行 gocqhttp：
```sh
$ cd gocqhttp
$ ./gocqhttp

[2020-11-11 02:51:37] [INFO]: 当前版本:v0.9.29-fix2
[2020-11-11 02:51:37] [WARNING]: 虚拟设备信息不存在, 将自动生成随机设备.
[2020-11-11 02:51:37] [INFO]: 已生成设备信息并保存到 device.json 文件.
[2020-11-11 02:51:37] [INFO]: Bot将在5秒后登录并开始信息处理, 按 Ctrl+C 取消.
[2020-11-11 02:51:42] [INFO]: 开始尝试登录并同步消息...
[2020-11-11 02:51:42] [INFO]: 使用协议: Android Pad
[2020-11-11 02:51:42] [INFO]: Protocol -> connect to server: ...
[2020-11-11 02:52:08] [INFO]: 登录成功 欢迎使用: ...
[2020-11-11 02:52:09] [INFO]: 开始加载好友列表...
```

此时和机器人打开私聊窗口，发送消息会得到回复：

![img](assets/privatechat.jpg)

打开一个群聊窗口：

![img](assets/groupchat.jpg)

尝试让其余群员发送相同的消息，机器人没有响应。

此时切换到终端，理应有新的 DEBUG 消息打印出来。

这样我们的 `lucia` 机器人就成功运行了。接下来我们就可以把重心放在机器人逻辑上了。
