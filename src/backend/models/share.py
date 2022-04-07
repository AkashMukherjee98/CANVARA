from sqlalchemy import and_
from sqlalchemy.orm import relationship, noload

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .user import User


class ShareItemType():  # pylint: disable=too-few-public-methods
    SUPPORTED_TYPES = [
        'gig',
        'offer',
        'position',
        'event',
        'community',
        'people'
    ]

    @classmethod
    def validate_and_return_item_type(cls, item_type):
        if item_type not in cls.SUPPORTED_TYPES:
            raise InvalidArgumentError(f"Unsupported item type: {item_type}")
        return item_type


class Share(ModelBase):
    __tablename__ = 'share'

    share_by = relationship(User, foreign_keys="[Share.share_by_user_id]")
    share_with_users = relationship(User, primaryjoin='User.id == any_(foreign(Share.share_with_user_ids))', uselist=True)

    item_gig = relationship("Post", foreign_keys="[Share.item_id]", primaryjoin=("Share.item_id == Post.id"))
    item_offer = relationship("Offer", foreign_keys="[Share.item_id]", primaryjoin=("Share.item_id == Offer.id"))
    item_position = relationship("Position", foreign_keys="[Share.item_id]", primaryjoin=("Share.item_id == Position.id"))
    item_event = relationship("Event", foreign_keys="[Share.item_id]", primaryjoin=("Share.item_id == Event.id"))
    item_community = relationship("Community", foreign_keys="[Share.item_id]", primaryjoin=("Share.item_id == Community.id"))
    item_people = relationship("User", foreign_keys="[Share.item_id]", primaryjoin=("Share.item_id == User.id"))

    def as_dict(self):
        share = {
            'share_id': self.id,
            'share_by': self.share_by.as_summary_dict(),
            'created_at': self.created_at.isoformat(timespec='milliseconds')
        }

        if self.share_with_users:
            share['share_with_users'] = [
                share_with_user.as_summary_dict() for share_with_user in self.share_with_users]

        share['item_type'] = self.item_type
        share['item'] = None
        if self.item_type == "gig":
            share['item'] = self.item_gig.as_custom_dict()
        elif self.item_type == "offer":
            share['item'] = self.item_offer.as_dict(['overview_text'])
        elif self.item_type == "position":
            share['item'] = self.item_position.as_dict()
        elif self.item_type == "event":
            share['item'] = self.item_event.as_summary_dict()
        elif self.item_type == "community":
            share['item'] = self.item_community.as_summary_dict()
        elif self.item_type == "people":
            share['item'] = self.item_people.as_summary_dict()

        def add_if_not_none(key, value):
            if value is not None:
                share[key] = value

        add_if_not_none('message', self.message)

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
        shares = tx.query(cls).where(
            Share.share_with_user_ids.any(user.id)
        ).order_by(Share.created_at.desc())

        if limit is not None:
            shares = shares.limit(int(limit))

        query_options = [
            noload(Share.share_with_users)
        ]

        shares = shares.options(query_options)
        return shares
