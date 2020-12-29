import asyncio
from datetime import datetime
from typing import Optional

from .broadcast import TPayload, broadcast
from .log import logger


_counts = [0 for _ in range(61)]

_epoch = datetime.now()


def _get_offset() -> int:
    return int((datetime.now() - _epoch).total_seconds()) % 61


async def get_count(curr_s: Optional[int] = None) -> TPayload:
    'Gets report that counts number of messages received in last 60s and last second.'
    if curr_s is None:
        curr_s = _get_offset()
    return {
        'type': 'messageLoad',
        'data': {
            'lastMin': sum(_counts),
            'lastSec': _counts[curr_s - 1], # note [-1] indexes to [60]!
        },
    }


async def increase_now():
    _counts[_get_offset()] += 1


async def init():
    'Kickstarts the message counting service (removing old counts) and brocasting.'
    loop = asyncio.get_event_loop()
    def _service():
        curr_s = _get_offset()
        # 归零第 61 秒前的计数
        _counts[curr_s + 1 if curr_s != 60 else 0] = 0
        # 把计数消息广播出去，然后等一秒钟再继续这个循环
        # logger.info('reset')  # 取消试试
        asyncio.create_task(broadcast(lambda: get_count(curr_s)))
        loop.call_at(int(loop.time()) + 1, _service)

    _service()

    logger.info('Message load count loaded successfully!')
