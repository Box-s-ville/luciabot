import json
from quart import Quart, websocket, send_file

from service_config import RESOURCES_DIR
from services import command_use_count, inmsg_count
from services.broadcast import listen_to_broadcasts


def add_controllers(app: Quart):

    @app.route('/dashboard', ['GET'])
    async def _dashboard_get():
        return await send_file(f'{RESOURCES_DIR}/dashboard.html')

    @app.websocket('/expose')
    async def _expose_ws():
        # 主动调用 API，填充完整的命令调用信息 (bootstrap)
        await websocket.send(json.dumps(await inmsg_count.get_count()))
        await websocket.send(json.dumps(await command_use_count.get_count()))
        # 然后再接入消息队列被动获取信息
        with listen_to_broadcasts('messageLoad', 'pluginUsage') as get:
            while True:
                payload = await get()
                await websocket.send(json.dumps(payload))

