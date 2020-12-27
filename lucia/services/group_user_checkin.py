import random
from datetime import datetime

from .log import logger
from .db_context import db
from models.group_user import GroupUser


async def group_user_check_in(user_qq: int, group: int) -> str:
    'Returns string describing the result of checking in'
    present = datetime.now()
    async with db.transaction():
        user = await GroupUser.ensure(user_qq, group)
        # 如果同一天签到过，特殊处理
        if user.checkin_time_last.date() == present.date():
            return _handle_already_checked_in(user)
        return await _handle_check_in(user, present) # ok


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


async def group_user_check(user_qq: int, group: int) -> str:
    # heuristic: if users find they have never checked in they are probable to check in
    user = await GroupUser.ensure(user_qq, group)
    return '好感度：{:.2f}\n历史签到数：{}\n上次签到日期：{}'.format(
        user.impression,
        user.checkin_count,
        user.checkin_time_last.strftime('%Y-%m-%d') if user.checkin_time_last != datetime.min else '从未',
    )
