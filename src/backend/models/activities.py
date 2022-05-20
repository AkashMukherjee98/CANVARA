from .user import User

from .post import Post
from .application import Application
from .offer import Offer
from .offer import OfferProposal

from .community import Community, CommunityMembership
from .event import Event, EventRSVP


class MyActivity():
    @classmethod
    def own_gigs(cls, tx, user):  # pylint: disable=unused-argument
        return list()

    @classmethod
    def own_offers(cls, tx, user):  # pylint: disable=unused-argument
        return list()

    @classmethod
    def own_positions(cls, tx, user):  # pylint: disable=unused-argument
        return list()

    @classmethod
    def my_applications(cls, tx, user, status):
        applications = tx.query(Application).join(Post).where(
            Post.id == Application.post_id,
            Application.user_id == user.id,
            Application.status.in_(status)
        )
        return list(applications)

    @classmethod
    def my_proposals(cls, tx, user, status):
        proposals = tx.query(OfferProposal).join(Offer).where(
            Offer.id == OfferProposal.offer_id,
            OfferProposal.proposer_id == user.id,
            OfferProposal.status.in_(status)
        )
        return list(proposals)

    @classmethod
    def my_communities(cls, tx, user):
        communities = tx.query(Community).join(CommunityMembership).where(
            Community.status == 'active',
            CommunityMembership.member_id == user.id
        )
        return list(communities)

    @classmethod
    def my_events(cls, tx, user):
        events = tx.query(Event).join(EventRSVP).where(
            Event.status == 'active',
            EventRSVP.guest_id == user.id
        )
        return list(events)

    @classmethod
    def my_connections(cls, tx, user):
        users = tx.query(User).join(CommunityMembership).where(
            CommunityMembership.member != user,
            CommunityMembership.member_id == User.id,
            CommunityMembership.community_id.in_(tx.query(CommunityMembership.community_id).where(
                CommunityMembership.member == user
            ).subquery())
        )
        return list(users)
