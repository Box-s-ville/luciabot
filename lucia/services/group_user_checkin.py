import asyncio
import random
from datetime import datetime
from io import BytesIO
from base64 import b64encode

from PIL import Image, ImageDraw, ImageFont

from .log import logger
from .db_context import db
from .processpool import processpool_executor
from service_config import RESOURCES_DIR
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


async def group_user_check_use_b64img(user_qq: int, group: int, user_name: str) -> str:
    'Returns the base64 image representation of the user check result.'
    user = await GroupUser.ensure(user_qq, group)

    # expensive operation!
    return await asyncio.get_event_loop().run_in_executor(
        processpool_executor,
        _create_user_check_b64img,
        user_name, user,
    )


def _create_user_check_b64img(user_name: str, user: GroupUser) -> str:
    # TODO: we have a lot of byte copies. we have to optimise them.
    bg_dir = f'{RESOURCES_DIR}/group_user_check_bg.png'
    font_dir = f'{RESOURCES_DIR}/SourceHanSans-Regular.otf'

    image = Image.open(bg_dir)
    draw = ImageDraw.ImageDraw(image)
    font_title = ImageFont.truetype(font_dir, 33 if len(user_name) < 8 else 28)
    font_detail = ImageFont.truetype(font_dir, 22)

    txt_user = f'{user_name} ({user.user_qq})'
    draw.text((530, 65), txt_user, fill=(255, 255, 255), font=font_title, stroke_width=1, stroke_fill='#7042ad')

    txt_detail = (
        f'群: {user.belonging_group}\n'
        f'好感度: {user.impression:.02f}\n'
        f'签到次数: {user.checkin_count}\n'
        f'上次签到: {user.checkin_time_last.strftime("%Y-%m-%d") if user.checkin_count else "从未"}'
    )
    draw.text((530, 115), txt_detail, fill=(255, 255, 255), font=font_detail, stroke_width=1, stroke_fill='#75559e')

    buff = BytesIO()
    image.save(buff, 'jpeg')
    return b64encode(buff.getvalue()).decode()
