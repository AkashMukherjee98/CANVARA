from enum import Enum
import copy

from sqlalchemy import and_
from sqlalchemy.orm import relationship, noload

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
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
    def search(cls, tx, user, limit=None):  # pylint: disable=too-many-arguments
        if limit is not None:
            offers = tx.query(cls).where(and_(
                User.customer_id == user.customer_id,
                cls.status == OfferStatus.ACTIVE.value
            )).limit(limit)
        else:
            offers = tx.query(cls).where(and_(
                User.customer_id == user.customer_id,
                cls.status == OfferStatus.ACTIVE.value
            ))

        query_options = [
            noload(Offer.offer_overview_video)
        ]

        offers = offers.options(query_options)
        return offers


class OfferProposalStatus(Enum):
    NEW = 'new'
    UNDER_REVIEW = 'under_review'
    SELECTED = 'selected'
    REJECTED = 'rejected'
    IN_PROGRESS = 'in_progress'
    SUSPENDED = 'suspended'
    COMPLETED = 'completed'
    DELETED = 'deleted'

    @classmethod
    def lookup(cls, proposal_status):
        if proposal_status is None:
            return None

        try:
            return cls(proposal_status.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid proposal status: {proposal_status}.") from ex


class OfferProposal(ModelBase):
    __tablename__ = 'offer_proposal'

    proposer = relationship(User, foreign_keys="[OfferProposal.proposer_id]")
    offer = relationship(Offer, foreign_keys="[OfferProposal.offer_id]")
    proposal_overview_video = relationship(UserUpload, foreign_keys="[OfferProposal.overview_video_id]")
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

        self.details = details

    def as_dict(self):
        proposal = {
            'proposal_id': self.id,
            'name': self.name,
            'proposer': self.proposer.as_precis_dict(),
            'offer_id': self.offer.id,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

        if self.proposal_overview_video:
            proposal['overview_video'] = self.proposal_overview_video.as_dict(method='get')

        def add_if_not_none(key, value):
            if value is not None:
                proposal[key] = value

        add_if_not_none('overview_text', self.details.get('overview_text'))

        add_if_not_none('proposer_feedback', self.proposer_feedback)
        add_if_not_none('proposer_feedback_at', self.proposer_feedback_at.isoformat() if self.proposer_feedback_at else None)

        add_if_not_none('offerer_feedback', self.offerer_feedback)
        add_if_not_none('offerer_feedback_at', self.offerer_feedback_at.isoformat() if self.offerer_feedback_at else None)

        add_if_not_none('decided_at', self.decided_at.isoformat() if self.decided_at else None)
        add_if_not_none('closed_at', self.closed_at.isoformat() if self.closed_at else None)

        return proposal

    @classmethod
    def lookup(cls, tx, proposal_id, must_exist=True):
        proposal = tx.query(cls).where(and_(
            cls.id == proposal_id,
            cls.status != OfferProposalStatus.DELETED.value
        )).one_or_none()
        if proposal is None and must_exist:
            raise DoesNotExistError(f"Proposal '{proposal_id}' does not exist")
        return proposal

    @classmethod
    def search(cls, tx, user, offer_id):  # pylint: disable=too-many-arguments
        proposals = tx.query(cls).where(and_(
            User.customer_id == user.customer_id,
            cls.offer_id == offer_id,
            cls.status != OfferProposalStatus.DELETED.value
        ))
        query_options = [
            noload(OfferProposal.proposal_overview_video)
        ]

        proposals = proposals.options(query_options)
        return proposals
