from enum import Enum
import copy

from sqlalchemy import and_
from sqlalchemy.orm import relationship, noload

from backend.common.exceptions import DoesNotExistError
from .db import ModelBase
from .user import User
from .user_upload import UserUpload


class OfferStatus(Enum):
    # Offer is available for proposer

    ACTIVE = 'active'

    # Offer has been deleted
    DELETED = 'deleted'


class Offer(ModelBase):
    __tablename__ = 'offer'

    offerer = relationship(User, foreign_keys="[Offer.offerer_id]")
    offer_overview_video = relationship(UserUpload, foreign_keys="[Offer.overview_video_id]")
    details = None

    def update_details(self, payload):
        details = copy.deepcopy(self.details) if self.details else {}
        details_fields = [
            'overview_text'
        ]

        for field_item in details_fields:
            if payload.get(field_item) is not None:
                if payload[field_item]:
                    details[field_item] = payload[field_item]
                elif field_item in details:
                    del details[field_item]

        if payload.get('hashtags') is not None:
            if payload['hashtags']:
                details['hashtags'] = payload['hashtags']
            elif 'hashtags' in details:
                del details['hashtags']

        self.details = details

    def as_dict(self):
        offer = {
            'offer_id': self.id,
            'name': self.name,
            'offerer': self.offerer.as_summary_dict(),
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'last_updated_at': self.last_updated_at.isoformat()
        }

        if self.offer_overview_video:
            offer['overview_video'] = self.offer_overview_video.as_dict(method='get')

        def add_if_not_none(key, value):
            if value is not None:
                offer[key] = value

        add_if_not_none('hashtags', self.details.get('hashtags'))
        add_if_not_none('overview_text', self.details.get('overview_text'))

        return offer

    @classmethod
    def lookup(cls, tx, offer_id, must_exist=True):
        offer = tx.query(cls).where(and_(
            cls.id == offer_id,
            cls.status == OfferStatus.ACTIVE.value
        )).one_or_none()
        if offer is None and must_exist:
            raise DoesNotExistError(f"Offer '{offer_id}' does not exist")
        return offer

    @classmethod
    def search(cls, tx, user):  # pylint: disable=too-many-arguments
        offers = tx.query(cls).where(and_(
            User.customer_id == user.customer_id,
            cls.status == OfferStatus.ACTIVE.value
        ))

        query_options = [
            noload(Offer.offer_overview_video)
        ]

        offers = offers.options(query_options)

        return offers
