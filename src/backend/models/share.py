from sqlalchemy import and_, or_, cast, Boolean
from sqlalchemy.orm import relationship, noload, contains_eager

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .user import User
from .post import Post


class Share(ModelBase):
    __tablename__ = 'share'

    shared_by = relationship(User, foreign_keys="[Share.shared_by_user_id]")
    shared_with = relationship(User, foreign_keys="[Share.shared_with_user_id]")
    item = relationship(Post, foreign_keys="[Share.item_id]", primaryjoin=(
        "or_(Share.item_id == Post.id, Share.item_id == Offer.id)"))
    '''item = relationship("EventRSVP", primaryjoin=(
        "and_(EventRSVP.event_id==Event.id, "
        "or_(EventRSVP.status == 'yes', "
        "EventRSVP.status == 'no', "
        "EventRSVP.status == 'maybe'))"))'''

    def as_dict(self):
        share = {
            'share_id': self.id,
            'shared_by': self.shared_by.as_summary_dict(),
            'created_at': self.created_at.isoformat(timespec='milliseconds')
        }

        def add_if_not_none(key, value):
            if value is not None:
                share[key] = value

        add_if_not_none('notes', self.notes)

        return share

    @classmethod
    def lookup(cls, tx, share_id, must_exist=True):
        share = tx.query(cls).where(and_(
            cls.id == share_id
        )).one_or_none()
        if share is None and must_exist:
            raise DoesNotExistError(f"Share '{share_id}' item does not exist")
        return share

    @classmethod
    def search(cls, tx, user, limit=None):  # pylint: disable=too-many-arguments, disable=too-many-branches
        shares = tx.query(cls).where(and_(
            Share.shared_with_user_id != user.id
        ))

        if limit is not None:
            shares = shares.limit(int(limit))

        query_options = [
            noload(Share.shared_with)
        ]

        shares = shares.options(query_options)
        return shares