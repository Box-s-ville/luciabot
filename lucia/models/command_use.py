import datetime

from services.db_context import db


class CommandUse(db.Model):
    __tablename__ = 'command_uses'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    date = db.Column(db.Date(), nullable=False)

    use_count = db.Column(db.Integer(), nullable=False)

    _idx1 = db.Index('command_uses_idx1', 'name', 'date', unique=True)

    @classmethod
    async def ensure(cls, name: str, date: datetime.date, for_update: bool = False) -> 'CommandUse':
        query = cls.query.where((cls.name == name) & (cls.date == date))
        if for_update:
            query = query.with_for_update()
        data = await query.gino.first()

        return data or await cls.create(
            name=name,
            date=date,
            use_count=0,
        )
