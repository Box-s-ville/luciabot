# luciabot on [NoneBot](https://github.com/nonebot/nonebot)
[![License](https://img.shields.io/github/license/nonebot/nonebot.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Docker](https://img.shields.io/badge/Docker-19%2B-blue.svg)

This tutorial demonstrates how to build a QQ robot using [NoneBot](https://github.com/nonebot/nonebot) and [gocqhttp](https://github.com/Mrs4s/go-cqhttp/) from scratch using the non-so-strict "Model-Control-Service" architecture. After reading the guide and trying the code, the reader should be able to deploy a mini feature-rich robot that can serve on a desktop or a server.

Project is for demo only! Do not take it seriously (i.e. relying on it on production without tweaks).

The guide advances through these chapters:
* [Document 1](guide/New%20Text%20Document.md) - 搭建可以運行的機器人
  * 完成最基本的 NoneBot 和 gocqhttp 的配置，并且編寫最簡單的 `ping` 命令
* [Document 2](guide/New%20Text%20Document%202.md) - 編寫插件
  * 調用第三方天氣 API 實現天氣功能，使用 NoneBot 的命令機制和自然語言處理器 ([jieba](https://github.com/fxsjy/jieba)) 當用戶詢問時將結果返回給用戶
* [Document 3](guide/New%20Text%20Document%203.md) - 對接第三方數據庫
  * 使用 [docker-compose](https://docs.docker.com/compose/) 打包機器人和 [PostgresSQL](https://www.postgresql.org/) 組件。透過 [Gino](https://github.com/python-gino/gino) Model 和 [Pillow](https://pillow.readthedocs.io/en/stable/) 繪圖庫搭配 NoneBot 實現簽到功能
* [Document 4](guide/New%20Text%20Document%204.md) - 搭建消息監控
  * 運用 NoneBot 自帶的 [Quart](https://pgjones.gitlab.io/quart/) 和 [asyncio](https://docs.python.org/3/library/asyncio.html) 編寫消息傳遞機制來實現實時更新的 HTML 監控面板。同時實現交互複雜的 `tty` 命令
* [Document 5](guide/New%20Text%20Document%205.md) - 尾聲
  * 初試 NoneBot 好友請求處理器；為機器人撰寫説明命令。為教程收尾

## Licensing
You should read [The license](./LICENSE) before proceeding.

Please email or submit an issue if you have any questions regarding licenses or copyrights.

## Running the project
Clone the project
```
git clone https://github.com/Box-s-ville/luciabot && cd luciabot
```

Go to [gocqhttp/config.yml](./gocqhttp/config.yml) and modify the robot's qq and password.

A [docker](https://www.docker.com/products/docker-desktop) environment is preferred. Deploying this app using docker is easy.

```
docker-compose build
docker-compose up
```

Which are exactly the same procedures described in the guide section.

## Inaccuracies
The tutorial (and the dependencies of the project) goes not guarantee to be most precise or up-to-date. If any incompatibilities, errors and bugs are present, you can submit an [issue](https://github.com/Box-s-ville/luciabot/issues) or open a [pull request](https://github.com/Box-s-ville/luciabot/pulls). Help is appreciated.
