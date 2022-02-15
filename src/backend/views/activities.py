from flask import jsonify
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from sqlalchemy import select

from backend.views.base import AuthenticatedAPIBase
from backend.models.db import transaction
from backend.models.user import User
from backend.models.post import Post, PostFilter
from backend.models.application import ApplicationStatus
from backend.models.offer import OfferProposalStatus
from backend.models.activities import MyActivity


blueprint = Blueprint('myactivities', __name__, url_prefix='/myactivities')


@blueprint.route('/')
class MyActivityAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            own_gigs = MyActivity.own_gigs(tx, user)
            own_offers = MyActivity.own_offers(tx, user)
            own_positions = MyActivity.own_positions(tx, user)

            act_gigs = MyActivity.act_gigs(tx, user, [])
            my_proposals = MyActivity.my_proposals(tx, user, [
                OfferProposalStatus.NEW.value,
                OfferProposalStatus.ACTIVE_READ.value])

            application_tasks = MyActivity.my_applications(tx, user, [
                ApplicationStatus.SELECTED.value])
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
                    'gigs': [gig.as_dict() for gig in own_gigs],
                    'offers': [offer.as_dict() for offer in own_offers],
                    'positions': [position.as_dict() for position in own_positions]
                },
                'applications': {
                    'gigs': [gig.as_dict() for gig in act_gigs],
                    'proposals': [proposal.as_dict() for proposal in my_proposals]
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
