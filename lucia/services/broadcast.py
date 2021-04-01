import asyncio
from contextlib import contextmanager
from typing import Any, Awaitable, Callable, Generator


# 约定所有通过队列的消息都要遵从此格式
# {
#   type: string,
#   data: any,
# }
TPayload = dict[str, Any]

# 目前存在的消息队列，一个客户（websocket 连接）对应着一个队列
# 键为队列，值为所监听的消息类型
_listeners: dict[asyncio.Queue[TPayload], set[str]] = {}


@contextmanager
def listen_to_broadcasts(*types: str) -> Generator[Callable[[], Awaitable[TPayload]], None, None]:
    'Returns a callable that when called, receives new messages.'
    queue = asyncio.Queue()
    _listeners[queue] = set(types)
    try:
        yield queue.get
    finally:
        _listeners.pop(queue)


async def broadcast(type_: str, data_lazy: Callable[[], Awaitable[Any]]):
    'Tag and broadcast messages to all current subscribers.'
    qs = [queue for queue, types in _listeners.items() if type_ in types]
    if qs:
        payload = as_payload(type_, await data_lazy())
        await asyncio.gather(*[queue.put(payload) for queue in qs])


def as_payload(type_: str, data: Any) -> TPayload:
    'Wrap a result into a payload.'
    return {
        'type': type_, 'data': data
    }
