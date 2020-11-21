import random
from datetime import datetime

from services.db_context import db
from models.group_user import GroupUser


async def group_user_sign_in(user_qq: int, group: int) -> str:
    'Returns string describing the result of signing in'
    present = datetime.now()
    async with db.transaction():
        user = await GroupUser.ensure(user_qq, group)
        # 如果同一天签到过，特殊处理
        if user.signin_time_last.date() == present.date():
            return _handle_already_signed_in(user)
        return await _handle_sign_in(user, present) # ok


def _handle_already_signed_in(user: GroupUser) -> str:
    return f'已经签到过啦~ 好感度：{user.love:.2f}'


async def _handle_sign_in(user: GroupUser, present: datetime) -> str:
    love_added = random.random()
    new_love = user.love + love_added
    message = random.choice((
        '谢谢，你是个好人！',
        '对了，来喝杯茶吗？',
    ))

    await user.update(
        signin_count=user.signin_count + 1,
        signin_time_last=present,
        love=new_love,
    ).apply()

    return f'{message} 好感度：{new_love:.2f} (+{love_added:.2f})'


async def group_user_check(user_qq: int, group: int) -> str:
    # heuristic: if users find they have never signed in they are probable to sign in
    user = await GroupUser.ensure(user_qq, group)
    return '好感度：{:.2f}\n历史签到数：{}\n上次签到日期：{}'.format(
        user.love,
        user.signin_count,
        user.signin_time_last.strftime('%Y-%m-%d') if user.signin_time_last != datetime.min else '从未',
    )
