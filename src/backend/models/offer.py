from enum import Enum
import copy

from sqlalchemy import and_, or_
from sqlalchemy.orm import relationship, noload, contains_eager

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .user import User
from .user_upload import UserUpload


class OfferSortFilter(Enum):
    # Most relevant recommended offers for the user
    RECOMMENDED = 'recommended'

    # Latest active offers for the user
    LATEST = 'latest'

    @classmethod
    def lookup(cls, name):
        if name is None:
            return None

        try:
            return OfferSortFilter(name.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported Sorting option: {name}.") from ex


class OfferStatusFilter(Enum):
    # Offer is available for proposer
    ACTIVE = 'active'

    @classmethod
    def lookup(cls, name):
        if name is None:
            return None

        try:
            return OfferStatusFilter(name.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported status filter: {name}.") from ex


class OfferStatus(Enum):
    # Offer is available for proposer
    ACTIVE = 'active'

    # Offer has been deleted
    DELETED = 'deleted'


class Offer(ModelBase):
    __tablename__ = 'offer'

    offerer = relationship(User, foreign_keys="[Offer.offerer_id]")
    offer_overview_video = relationship(UserUpload, foreign_keys="[Offer.overview_video_id]")
    bookmark_users = relationship("OfferBookmark", back_populates="offer")
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

    def as_dict(self, return_keys=all):  # if return_keys=all return everything, if any key(s) specified then return those only
        offer = {
            'offer_id': self.id,
            'name': self.name
        }

        def add_if_required(key, value):
            if (return_keys is all or key in return_keys) and value is not None:
                offer[key] = value

        add_if_required(
            'offerer', self.offerer.as_custom_dict(['title', 'pronoun', 'location', 'department']) if self.offerer else None)

        add_if_required(
            'overview_video', self.offer_overview_video.as_dict(method='get') if self.offer_overview_video else None)

        add_if_required('hashtags', self.details.get('hashtags'))
        add_if_required('overview_text', self.details.get('overview_text'))
        add_if_required('status', self.status)
        add_if_required('created_at', self.created_at.isoformat() if self.created_at else None)
        add_if_required('last_updated_at', self.last_updated_at.isoformat() if self.last_updated_at else None)

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
    def search(cls, tx, user, sort=None, keyword=None, status=None, limit=None):  # pylint: disable=too-many-arguments
        offers = tx.query(cls).join(Offer.offerer).where(and_(
            User.customer_id == user.customer_id,
            Offer.offerer_id != user.id,
            cls.status == OfferStatus.ACTIVE.value
        ))

        if sort is not None and sort == OfferSortFilter.LATEST:
            offers = offers.order_by(Offer.created_at.desc())

        if keyword is not None:
            offers = offers.where(or_(
                Offer.name.ilike(f'%{keyword}%'),
                Offer.details['overview_text'].astext.ilike(f'%{keyword}%'),  # pylint: disable=unsubscriptable-object
                Offer.details['hashtags'].astext.ilike(f'%{keyword}%')  # pylint: disable=unsubscriptable-object
            ))

        if status == OfferStatusFilter.ACTIVE:
            offers = offers.where(and_(
                Offer.status == OfferStatus.ACTIVE.value
            ))

        if limit is not None:
            offers = offers.limit(int(limit))

        query_options = [
            noload(Offer.offer_overview_video)
        ]

        offers = offers.options(query_options)
        return offers

    @classmethod
    def my_bookmarks(
        cls, tx, user
    ):
        offers = tx.query(cls).where(and_(
            cls.status != OfferStatus.DELETED.value
        )).join(Offer.bookmark_users.and_(OfferBookmark.user_id == user.id)).\
            order_by(OfferBookmark.created_at.desc())

        query_options = [
            noload(Offer.offer_overview_video),
            contains_eager(Offer.bookmark_users)
        ]

        offers = offers.options(query_options)
        return offers


class OfferBookmark(ModelBase):  # pylint: disable=too-few-public-methods
    __tablename__ = 'offer_bookmark'

    user = relationship("User")
    offer = relationship("Offer", back_populates="bookmark_users")

    @classmethod
    def lookup(cls, tx, user_id, offer_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, offer_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Bookmark for offer '{offer_id}' and user '{user_id}' does not exist")
        return bookmark


class OfferProposalFilter(Enum):
    # All proposals except deleted
    ALL = 'all'

    # New and active_read applications
    ACTIVE = 'active'

    SELECTED = 'selected'
    REJECTED = 'rejected'
    IN_PROGRESS = 'in_progress'
    SUSPENDED = 'suspended'
    COMPLETED = 'completed'

    @classmethod
    def lookup(cls, proposal_filter):
        if proposal_filter is None:
            return None

        try:
            # For now jump to in_progress
            if proposal_filter == 'selected':
                proposal_filter = 'in_progress'

            return cls(proposal_filter.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported filter: {proposal_filter}.") from ex


class OfferProposalStatus(Enum):
    NEW = 'new'
    ACTIVE_READ = 'active_read'
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
            # For now jump to in_progress
            if proposal_status == 'selected':
                proposal_status = 'in_progress'

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
            'name': self.name
        }

        def add_if_not_none(key, value):
            if value is not None:
                proposal[key] = value

        add_if_not_none('offer_id', self.offer_id)  # Need to remove, deprecated
        add_if_not_none('offer', self.offer.as_dict([
            'offerer', 'hashtags', 'status', 'created_at', 'last_updated_at'
            ]) if self.offer else None)
        add_if_not_none('proposer', self.proposer.as_custom_dict([
            'title', 'pronoun', 'location', 'department', 'email', 'phone_number', 'slack_teams_messaging_id'
            ]) if self.proposer else None)

        add_if_not_none('overview_text', self.details.get('overview_text'))
        add_if_not_none(
            'overview_video', self.proposal_overview_video.as_dict(method='get') if self.proposal_overview_video else None)

        add_if_not_none('proposer_feedback', self.proposer_feedback)
        add_if_not_none('proposer_feedback_at', self.proposer_feedback_at.isoformat() if self.proposer_feedback_at else None)

        add_if_not_none('offerer_feedback', self.offerer_feedback)
        add_if_not_none('offerer_feedback_at', self.offerer_feedback_at.isoformat() if self.offerer_feedback_at else None)

        add_if_not_none('status', self.status)
        add_if_not_none('decided_at', self.decided_at.isoformat() if self.decided_at else None)
        add_if_not_none('closed_at', self.closed_at.isoformat() if self.closed_at else None)
        add_if_not_none('created_at', self.created_at.isoformat() if self.created_at else None)
        add_if_not_none('last_updated_at', self.last_updated_at.isoformat() if self.last_updated_at else None)

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
    def search(cls, tx, user, offer_id, proposal_filter=None):  # pylint: disable=too-many-arguments
        proposals = tx.query(cls).where(and_(
            User.customer_id == user.customer_id,
            cls.offer_id == offer_id,
            cls.status != OfferProposalStatus.DELETED.value
        ))

        if proposal_filter == OfferProposalFilter.ACTIVE:
            proposals = proposals.where(cls.status.in_([
                OfferProposalStatus.NEW.value, OfferProposalStatus.ACTIVE_READ.value]))
        elif proposal_filter == OfferProposalFilter.SELECTED:
            proposals = proposals.where(cls.status == OfferProposalStatus.SELECTED.value)
        elif proposal_filter == OfferProposalFilter.REJECTED:
            proposals = proposals.where(cls.status == OfferProposalStatus.REJECTED.value)
        elif proposal_filter == OfferProposalFilter.IN_PROGRESS:
            proposals = proposals.where(cls.status == OfferProposalStatus.IN_PROGRESS.value)
        elif proposal_filter == OfferProposalFilter.SUSPENDED:
            proposals = proposals.where(cls.status == OfferProposalStatus.SUSPENDED.value)
        elif proposal_filter == OfferProposalFilter.COMPLETED:
            proposals = proposals.where(cls.status == OfferProposalStatus.COMPLETED.value)

        query_options = [
            noload(OfferProposal.proposal_overview_video)
        ]

        proposals = proposals.options(query_options)
        return proposals
