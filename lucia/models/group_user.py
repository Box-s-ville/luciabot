from datetime import datetime

from services.db_context import db


class GroupUser(db.Model):
    __tablename__ = 'group_users'

    id = db.Column(db.Integer(), primary_key=True)
    user_qq = db.Column(db.BigInteger(), nullable=False)
    belonging_group = db.Column(db.BigInteger(), nullable=False)

    signin_count = db.Column(db.Integer(), nullable=False)
    signin_time_last = db.Column(db.DateTime(timezone=True), nullable=False)
    love = db.Column(db.Numeric(scale=3, asdecimal=False), nullable=False)

    _idx1 = db.Index('group_users_idx1', 'user_qq', 'belonging_group', unique=True)

    @classmethod
    async def ensure(cls, user_qq: int, belonging_group: int) -> 'GroupUser':
        user = await cls.query.where(
            (cls.user_qq == user_qq) & (cls.belonging_group == belonging_group)
        ).gino.first()

        return user or await cls.create(
            user_qq=user_qq,
            belonging_group=belonging_group,
            signin_count=0,
            signin_time_last=datetime.min, # 从未签到过
            love=0,
        )
