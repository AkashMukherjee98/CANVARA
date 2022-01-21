from enum import Enum

from sqlalchemy import or_

from backend.common.exceptions import InvalidArgumentError

from .post import Post
from .application import Application
from .offer import Offer, OfferProposal
from .community import Community, CommunityMembership
from .event import Event, EventRSVP


class MarketplaceSort(Enum):
    RECOMMENDED = 'recommended'
    LATEST = 'latest'

    DEFAULT_LIMIT = 5

    @classmethod
    def lookup(cls, term):
        if term is None:
            return None

        try:
            return MarketplaceSort(term.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported filter: {term}.") from ex


class MyActivity():
    @classmethod
    def my_gigs(cls, tx, user):
        gigs = tx.query(Post).where(
            Post.owner_id == user.id
        )
        return list(gigs)

    @classmethod
    def my_applications(cls, tx, user, status):
        applications = tx.query(Application).where(
            Application.user_id == user.id,
            Application.status.in_(status)
        )
        return list(applications)

    @classmethod
    def my_offers(cls, tx, user):
        offers = tx.query(Offer).where(
            Offer.offerer_id == user.id
        )
        return list(offers)

    @classmethod
    def my_proposals(cls, tx, user, status):
        proposals = tx.query(OfferProposal).where(
            OfferProposal.proposer_id == user.id,
            OfferProposal.status.in_(status)
        )
        return list(proposals)

    @classmethod
    def my_communities(cls, tx, user):
        communities = tx.query(Community).join(CommunityMembership.member).where(or_(
            Community.primary_moderator_id == user.id,
            Community.secondary_moderator_id == user.id,
            Community.status == 'active' and
            CommunityMembership.member_id == user.id
        ))
        return list(communities)

    @classmethod
    def my_events(cls, tx, user):
        events = tx.query(Event).join(EventRSVP.guest).where(or_(
            Event.primary_organizer_id == user.id,
            Event.secondary_organizer_id == user.id,
            Event.status == 'active' and
            EventRSVP.member_id == user.id
        ))
        return list(events)
