import asyncio
import datetime
from functools import wraps
from typing import Awaitable, Callable, TypeVar

from .db_context import db
from .broadcast import broadcast
from models.command_use import CommandUse


_base_count: dict[str, int] = {}


async def get_count() -> dict[str, int]:
    'Gets all command use counts from the database for today.'
    today = datetime.datetime.today().date()
    re = await CommandUse \
        .select('name', 'use_count') \
        .where(CommandUse.date == today) \
        .gino.all()
    return _base_count | { pair['name']: pair['use_count'] for pair in re }


async def _get_count_incremental(usedata: CommandUse) -> dict[str, int]:
    return { usedata.name: usedata.use_count }


_TAsyncFunction = TypeVar('_TAsyncFunction', bound=Callable[..., Awaitable])


def record_successful_invocation(keyname: str):
    '''When the wrapped function exits, its today\'s use count is incremented and message
    is broadcasted.
    '''
    _base_count[keyname] = 0

    async def _post_invocation():
        # 记录调用
        today = datetime.datetime.today().date()
        async with db.transaction():
            usedata = await CommandUse.ensure(keyname, today, for_update=True)
            await usedata.update(use_count=usedata.use_count + 1).apply()
        # 仅广播增量信息！
        await broadcast('pluginUsage', lambda: _get_count_incremental(usedata))

    def decorator(f: _TAsyncFunction) -> _TAsyncFunction:
        @wraps(f)
        async def wrapped(*args, **kwargs):
            # 运行要调用被装饰的命令处理器
            result = await f(*args, **kwargs)
            # 然后做记录
            asyncio.create_task(_post_invocation())
            return result
        return wrapped # type: ignore

    return decorator
