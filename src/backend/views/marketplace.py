from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from sqlalchemy import select

from backend.views.base import AuthenticatedAPIBase
from backend.models.db import transaction
from backend.models.user import User
from backend.models.post import Post, PostFilter
from backend.models.application import ApplicationStatus
from backend.models.offer import Offer, OfferProposalStatus
from backend.models.position import Position
from backend.models.community import Community
from backend.models.event import Event
from backend.models.marketplace import MarketplaceSort, MyActivity


blueprint = Blueprint('marketplace', __name__, url_prefix='/marketplaces')


@blueprint.route('/opportunities')
class OpportunityAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        sort_by = request.args.get('sortby', None) or MarketplaceSort.RECOMMENDED.value
        MarketplaceSort.lookup(sort_by)

        limit = request.args.get('limit', None) or MarketplaceSort.DEFAULT_LIMIT.value

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            # Get list of gigs
            gigs = Post.search(
                tx,
                user,
                limit=int(limit)
            )

            # Get list of offers
            offers = Offer.search(
                tx,
                user,
                limit=int(limit)
            )

            # Get list of positions
            positions = Position.search(
                tx,
                user,
                limit=int(limit)
            )

            opportunities = {
                'gigs': [gig.as_dict(user=user) for gig in gigs],
                'offers': [offer.as_dict() for offer in offers],
                'positions': [position.as_dict() for position in positions]
            }
        return jsonify(opportunities)


@blueprint.route('/connections')
class ConnectionAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        sort_by = request.args.get('sortby', None) or MarketplaceSort.RECOMMENDED.value
        MarketplaceSort.lookup(sort_by)

        limit = request.args.get('limit', None) or MarketplaceSort.DEFAULT_LIMIT.value

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            # Get list of peoples
            peoples = tx.execute(select(User).where(User.customer_id == user.customer_id).limit(limit)).scalars().all()

            # Get list of communities
            communities = Community.search(
                tx,
                user,
                limit=int(limit)
            )

            # Get list of events
            events = Event.search(
                tx,
                user,
                limit=int(limit)
            )

            opportunities = {
                'peoples': [people.as_dict() for people in peoples],
                'communities': [community.as_dict() for community in communities],
                'events': [event.as_dict() for event in events]
            }
        return jsonify(opportunities)


@blueprint.route('/activities')
class MyActivityAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            gigs = MyActivity.my_gigs(tx, user)
            offers = MyActivity.my_offers(tx, user)

            applications = MyActivity.my_applications(tx, user, [
                ApplicationStatus.NEW.value,
                ApplicationStatus.SHORTLISTED.value])
            proposals = MyActivity.my_proposals(tx, user, [
                OfferProposalStatus.NEW.value,
                OfferProposalStatus.UNDER_REVIEW.value])

            application_tasks = MyActivity.my_applications(tx, user, [
                ApplicationStatus.SELECTED.value,
                ApplicationStatus.PASSED.value])
            proposal_tasks = MyActivity.my_proposals(tx, user, [
                OfferProposalStatus.SELECTED.value,
                OfferProposalStatus.IN_PROGRESS.value,
                OfferProposalStatus.COMPLETED.value])

            communities = MyActivity.my_communities(tx, user)
            events = MyActivity.my_events(tx, user)

            connections = tx.execute(select(User).where(User.customer_id == user.customer_id)).scalars().all()

            posts_bookmarks = Post.search(
                tx,
                user,
                post_filter=PostFilter.BOOKMARKED.value
            )

            activities = {
                'posts': {
                    'gigs': [gig.as_dict() for gig in gigs],
                    'offers': [offer.as_dict() for offer in offers]
                },
                'applications': {
                    'applications': [application.as_dict() for application in applications],
                    'proposals': [proposal.as_dict() for proposal in proposals]
                },
                'tasks': {
                    'applications': [application.as_dict() for application in application_tasks],
                    'proposals': [proposal.as_dict() for proposal in proposal_tasks]
                },
                'communities': [community.as_dict() for community in communities],
                'events': [event.as_dict() for event in events],
                'connections': [connection.as_dict() for connection in connections],
                'bookmarks': {
                    'gigs': [post.as_dict(user=user) for post in posts_bookmarks],
                    'offers': [],
                    'positions': [],
                    'community': [],
                    'events': [],
                    'peoples': []
                }
            }
        return jsonify(activities)
