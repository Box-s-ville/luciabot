# 使用 NoneBot 和 go-cqhttp 搭建 QQ 群聊机器人

接下来我们来实现一个签到插件。此插件因为要持久储存数据，需要一个数据库运行着。但是因为我们已经有了两个进程在运行了，再添一个就太乱了，所以需要一些办法来改善一下当前情况。

## 容器化机器人组件
在这里推荐遵循 [docker 官网](https://www.docker.com/products/docker-desktop) 的教程安装 docker。如果是在 Windows 10 或 mac 下，推荐使用 docker desktop。毕竟 UI 还是好用的。

安装好 docker 后，我们创建两个 Dockerfile，分别是机器人的前后端。

在目录 `luciabot/gocqhttp` 下，如果你是一路复制粘贴本文提到的代码的话，应该会包括至少两个文件：`go-cqhttp` 和 `config.json`。如果你运行过机器人，那么可能还会有其他运行时生成的文件例如 logs。

在此目录创建 `Dockerfile` 文件，内容如下：
```dockerfile
FROM alpine:3.12

WORKDIR /usr/src/app

RUN apk update && apk add tzdata

CMD [ "./go-cqhttp" ]
```
在这里使用的是 alpine linux 镜像直接运行这个二进制文件，相关文件之后挂载到镜像里。如有兴趣也可以参照 [官方的 repo](https://github.com/Mrs4s/go-cqhttp/blob/master/Dockerfile) 来自己编译运行 gocqhttp。

创建 `luciabot/lucia/Dockerfile`，内容如下：
```dockerfile
FROM python:3.9-alpine3.12

WORKDIR /usr/src/app

RUN apk update && apk add --virtual build-dependencies build-base gcc && apk add tzdata

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apk del build-dependencies

COPY . .

CMD [ "hypercorn", "bot:app", "-b", "0.0.0.0:8765" ]
```
Tip: 在这里我们没有直接运行 `bot.py` 而是使用了 asgi app（因为官方推荐这么做）。这种情况下机器人（Quart 框架）会读取在命令行这里传入的 IP 和端口，而无视 `bot_config.py` 的 IP 和端口。

在相同的目录下创建 `requirements.txt`：
```
nonebot==1.8.0
hypercorn==0.11.1
jieba==0.42.1
gino==1.0.1
```
本例用到的是 [gino orm](https://python-gino.org/) 来 CRUD 数据库。

我们需要同时开启三个应用程序，所以这里使用 compose 文件管理。创建 `luciabot/docker-compose.yml`：
```yml
version: '3'

services:
  # 用来运行 gocqhttp 二进制，注意这里目录是挂载的
  gocqhttp:
    container_name: gocqhttp
    environment:
      - TZ=Asia/Singapore
    tty: true
    stdin_open: true
    restart: always
    volumes:
      - ./gocqhttp:/usr/src/app:delegated
    build:
      context: ./gocqhttp

  # nonebot/quart
  lucia:
    container_name: lucia
    environment:
      - TZ=Asia/Singapore
      - DATABASE_URI=postgresql://root:password@postgres:5432/lucia
    ports:
      - 8765:8765
    depends_on:
      - postgres
    build:
      context: ./lucia

  # dev 数据库
  postgres:
    container_name: postgres
    environment:
      - TZ=Asia/Singapore
      - PGTZ=Asia/Singapore
      - POSTGRES_USER=root
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=lucia
    image: postgres:13.1-alpine

networks:
  default:
    name: luciabot-default
```

在这里我们组网，内有三个程序：gocqhttp 会挂载本地的硬盘目录，并且开启交互 shell（如果你已经登录过，可以不用），python39 和 postgres db。其中数据库提前定义好用户名和密码，并且将地址以环境变量的方式提供给 python39.

不要忘了同时修改 `luciabot/gocqhttp/config.json`：
```diff
  ...
  "ws_reverse_servers": [
    {
      "enabled": true,
-       "reverse_url": "ws://127.0.0.1:8765/ws",
+       "reverse_url": "ws://lucia:8765/ws",
      "reverse_api_url": "",
  ...
```

完毕后，运行如下命令：
```
$ docker compose build
$ docker compose up
```

你应该会在命令行中看到三个应用都启动了。

开启另一个命令行终端，输入以下命令
```sh
$ docker container ls

CONTAINER ID        IMAGE                  COMMAND                  PORTS                    NAMES
111111111111        luciabot_lucia         "hypercorn bot:app -…"   0.0.0.0:8765->8765/tcp   lucia
222222222222        postgres:13.1-alpine   "docker-entrypoint.s…"   5432/tcp                 postgres
333333333333        luciabot_gocqhttp      "./go-cqhttp"                                     gocqhttp
```
如上所示，我们可以看到运行中容器的信息。

如果 gocqhttp 需要你在命令行中输入内容（例如验证码），则运行如下命令：
```sh
$ docker attach 333333333333
```
来连接此进程的 tty，此时就可以输入东西了。操作完毕后，按 `Ctrl+P Ctrl+Q` 来结束当前 tty。在这之后你可以考虑移除 compose 文件中的 `tty` 和 `stdin_open`。

## 编写群签到服务
为了支持国产，尽管不太熟悉，我们还是义无反顾的选择（ 这个框架的 API 和 sqlalchemy 很像，上手来应该没有那麽多违和感）。

我们需要一个数据库连接单例，这样各模块就可以导入此全局对象来操作数据库了。我们仍然将此模块放在服务中，创建 `luciabot/lucia/services/db_context.py` 文件：
```py
import os

from gino import Gino

from .log import logger


# 全局数据库连接对象
db = Gino()


async def init():
    'Initialise psql database connection. Program must exit before the connection is freed.'
    uri = os.environ['DATABASE_URI']
    await db.set_bind(uri)
    await db.gino.create_all()
    logger.info(f'Database loaded successfully!')
```

这里定义了一个数据库初始化函数，其中先从环境变量中读取数据库地址，连接，再根据定义过的模型来在数据库里生成表。

那么在哪里定义签到表格和服务呢？最容易回答的问题。为了让表更容易被人和自动化工具识别，新建一个 `models` 文件夹，里面包含此文件：

`luciabot/lucia/models/group_user.py`
```py
from datetime import datetime

from services.db_context import db


class GroupUser(db.Model):
    __tablename__ = 'group_users'

    id = db.Column(db.Integer(), primary_key=True)
    user_qq = db.Column(db.BigInteger(), nullable=False)
    belonging_group = db.Column(db.BigInteger(), nullable=False)

    checkin_count = db.Column(db.Integer(), nullable=False)
    checkin_time_last = db.Column(db.DateTime(timezone=True), nullable=False)
    impression = db.Column(db.Numeric(scale=3, asdecimal=False), nullable=False)

    _idx1 = db.Index('group_users_idx1', 'user_qq', 'belonging_group', unique=True)
```

没什么好说的。其中 `impression` 是对应用户的签到积分。

为了方便，创建一个辅助函数用来“确保一个群用户（`GroupUser`）存在”，即如果存在则从数据库找到返回，否则用默认值创建一个新的。
```py
    # ...
    @classmethod
    async def ensure(cls, user_qq: int, belonging_group: int) -> 'GroupUser':
        user = await cls.query.where(
            (cls.user_qq == user_qq) & (cls.belonging_group == belonging_group)
        ).gino.first()

        return user or await cls.create(
            user_qq=user_qq,
            belonging_group=belonging_group,
            checkin_count=0,
            checkin_time_last=datetime.min, # 从未签到过
            impression=0,
        )
```

接下来就需要实现真正的签到函数了。我们创建文件 `luciabot/lucia/services/group_user_checkin.py`，添加以下的内容：
```py
import random
from datetime import datetime

from .log import logger
from .db_context import db
from models.group_user import GroupUser


async def group_user_check_in(user_qq: int, group: int) -> str:
    'Returns string describing the result of checking in'
    present = datetime.now()
    async with db.transaction():
        # 取得相应用户
        user = await GroupUser.ensure(user_qq, group)
        # 如果同一天签到过，特殊处理
        if user.checkin_time_last.date() == present.date():
            return _handle_already_checked_in(user)
        return await _handle_check_in(user, present) # ok
```

注意这里我们调用了 ORM model 来取得群聊的用户。使用一个对 `datetime.Date` 对象的比较此用户是不是在相同的一天签到过，如果签到过，则通知用户已经签到过，否则就处理此次签到。
```py
# ...
def _handle_already_checked_in(user: GroupUser) -> str:
    return f'已经签到过啦~ 好感度：{user.impression:.2f}'


async def _handle_check_in(user: GroupUser, present: datetime) -> str:
    impression_added = random.random()
    new_impression = user.impression + impression_added
    message = random.choice((
        '谢谢，你是个好人！',
        '对了，来喝杯茶吗？',
    ))

    await user.update(
        checkin_count=user.checkin_count + 1,
        checkin_time_last=present,
        impression=new_impression,
    ).apply()

    # 顺便打印此事件的日志
    logger.info(f'(USER {user.user_qq}, GROUP {user.belonging_group}) CHECKED IN successfully. score: {new_impression:.2f} (+{impression_added:.2f}).')

    return f'{message} 好感度：{new_impression:.2f} (+{impression_added:.2f})'
```
在这里生成一个处于 0 和 1 的随机数当作今天的积分值加到此用户并且更新签到日期为今天（所以如果再尝试签到的话就会失败）。仍然产生一个字符串标量返回。

Tip: 如果你想让此服务能被别处调用（例如网页），也可以让这些函数返回结构体。

我们顺便再定义一个使用户查询自己签到信息的函数：
```py
# ...
async def group_user_check(user_qq: int, group: int) -> str:
    # heuristic: if users find they have never checked in they are probable to check in
    user = await GroupUser.ensure(user_qq, group)
    return '好感度：{:.2f}\n历史签到数：{}\n上次签到日期：{}'.format(
        user.impression,
        user.checkin_count,
        user.checkin_time_last.strftime('%Y-%m-%d') if user.checkin_time_last != datetime.min else '从未',
    )
```

最后创建 NoneBot 的命令处理器：
```py
from nonebot.command import CommandSession
from nonebot.experimental.plugin import on_command

from services.group_user_checkin import group_user_check_in, group_user_check


__plugin_name__ = '签到'
__plugin_usage__ = (
    '用法：\n'
    '对我说 “签到” 来签到\n'
    '“我的签到” 来获取历史签到信息'
)


# 此功能只在群聊有效
checkin_permission = lambda sender: sender.is_groupchat


@on_command('签到', permission=checkin_permission)
async def _(session: CommandSession):
    await session.send(
        await group_user_check_in(session.event.user_id, session.event.group_id),
        at_sender=True,
    )


@on_command('我的签到', aliases={'好感度'}, permission=checkin_permission)
async def _(session: CommandSession):
    await session.send(
        await group_user_check(session.event.user_id, session.event.group_id),
        at_sender=True,
    )
```

内容直截了当。其中 `session.event` 包括当前会话状态中，发起者的详细信息，例如在这里我们可以得到发送者的 qq 号和所在群号。

最后的最后，不要忘记再主文件中初始化这一切：

`luciabot/lucia/bot.py`
```py
from os import path

import nonebot
import bot_config
from services import db_context


nonebot.init(bot_config)
nonebot.load_plugins(path.join(path.dirname(__file__), 'bot_plugins'), 'bot_plugins')

nonebot.on_startup(db_context.init) # 添加初始化函数作为服务器开始后的回调

# ... 略
```

键入 `docker-compose up`，找到一个群聊，我们来看实际的输出：
```
群主:
  莉西亚，好感度
lucia:
  @群主  好感度：0.00
  历史签到数：0
  上次签到日期：从未
群主:
  莉西亚，签到
lucia:
  @群主  对了，来喝杯茶吗？ 好感度：0.35 (+0.35)
群主:
  莉西亚，签到
lucia:
  @群主  已经签到过啦~ 好感度：0.35
群主:
  莉西亚，好感度
lucia:
  @群主  好感度：0.35
  历史签到数：1
  上次签到日期：2020-11-21
```

这是控制台输出的信息：
```
lucia       | [2020-12-27 11:18:24,936 lucia] INFO: (USER 123456789, GROUP 12345678) CHECKED IN successfully. score: 0.35 (+0.35).
```

重复的签到会失败，我们需要等到下一天才能签到下一次。

到这里，我们又完成了一个基于数据库的签到插件+积分系统。如果我们想，可以将此系统集成到其他的服务（插件）中，例如我们可以限制先前定义过的 weather 命令，使其在发送者不合规的情况下返回错误消息：
```py
    if (await GroupUser.ensure(user_qq, group)).impression < 50:
        return '我为什么要告诉你这个？'
    return '亲爱的，天气是：' + await get_current_weather_desc(city)
```

你可以使用自己的想象力，在这里我们就不展开了。

此时你的整个项目目录的结构应如下所示：
```
luciabot/
├── docker-compose.yml
├── gocqhttp/
│   ├── Dockerfile
│   ├── config.json
│   ├── go-cqhttp
└── lucia/
    ├── Dockerfile
    ├── bot.py
    ├── bot_config.py
    ├── bot_plugins/
    │   ├── group_user_checkin.py
    │   ├── ping.py
    │   └── weather.py
    ├── models/
    │   └── group_user.py
    ├── requirements.txt
    └── services/
        ├── common.py
        ├── db_context.py
        ├── group_user_checkin.py
        ├── log.py
        └── weather.py
```
注意这里省略了自动生成的临时文件。
