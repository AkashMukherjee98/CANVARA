from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from sqlalchemy import select

from backend.views.base import AuthenticatedAPIBase
from backend.models.db import transaction
from backend.common.exceptions import NotAllowedError
from backend.models.user import User
from backend.models.post import Post
from backend.models.offer import Offer
from backend.models.position import Position
from backend.models.community import Community
from backend.models.event import Event
from backend.models.marketplace import MarketplaceSort


blueprint = Blueprint('marketplace', __name__, url_prefix='/marketplaces')


@blueprint.route('/opportunities')
class OpportunityAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        sort_by = request.args.get('sortby')
        MarketplaceSort.lookup(sort_by)

        limit = request.args.get('limit')
        if not limit.isnumeric() or int(limit) < 0:
            raise NotAllowedError(f"Limit '{limit}' should be positive interger value.")

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            # Get list of gigs
            gigs = Post.search(
                tx,
                user
            )

            # Get list of offers
            offers = Offer.search(
                tx,
                user
            )

            # Get list of positions
            positions = Position.search(
                tx,
                user
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
        sort_by = request.args.get('sortby')
        MarketplaceSort.lookup(sort_by)

        limit = request.args.get('limit')
        if not limit.isnumeric() or int(limit) < 0:
            raise NotAllowedError(f"Limit '{limit}' should be positive interger value.")

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            # Get list of peoples
            peoples = tx.execute(select(User).where(User.customer_id == user.customer_id)).scalars().all()

            # Get list of communities
            communities = Community.search(
                tx,
                user
            )

            # Get list of events
            events = Event.search(
                tx,
                user
            )

            opportunities = {
                'peoples': [people.as_dict() for people in peoples],
                'communities': [community.as_dict() for community in communities],
                'events': [event.as_dict() for event in events]
            }
        return jsonify(opportunities)
