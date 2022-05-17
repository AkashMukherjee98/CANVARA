from backend.models.position import Position

from .post import Post
from .application import Application
from .offer import Offer, OfferProposal


class MyActivity():
    @classmethod
    def own_gigs(cls, tx, user):
        gigs = tx.query(Post).where(
            Post.owner_id == user.id
        )
        return list(gigs)

    @classmethod
    def own_offers(cls, tx, user):
        offers = tx.query(Offer).where(
            Offer.offerer_id == user.id
        )
        return list(offers)

    @classmethod
    def own_positions(cls, tx, user):
        positions = tx.query(Position).where(
            Position.manager_id == user.id
        )
        return list(positions)

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
    def my_communities(cls, tx, user):  # pylint: disable=unused-argument
        return list()

    @classmethod
    def my_events(cls, tx, user):  # pylint: disable=unused-argument
        return list()

    @classmethod
    def my_connections(cls, tx, user):  # pylint: disable=unused-argument
        return list()
