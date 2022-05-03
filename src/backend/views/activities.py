from flask import jsonify
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.views.base import AuthenticatedAPIBase
from backend.models.db import transaction
from backend.models.user import User
from backend.models.post import Post
from backend.models.application import ApplicationStatus
from backend.models.offer import Offer, OfferProposalStatus
from backend.models.position import Position
from backend.models.community import Community
from backend.models.event import Event
from backend.models.activities import MyActivity


blueprint = Blueprint('myactivities', __name__, url_prefix='/myactivities')


@blueprint.route('')
class MyActivityAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():  # pylint: disable=too-many-locals
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            # TODO: (santanu) Move methods to respective models
            own_gigs = MyActivity.own_gigs(tx, user)
            own_offers = MyActivity.own_offers(tx, user)
            own_positions = MyActivity.own_positions(tx, user)

            my_applications = MyActivity.my_applications(tx, user, [
                ApplicationStatus.NEW.value,
                ApplicationStatus.ACTIVE_READ.value])
            my_proposals = MyActivity.my_proposals(tx, user, [
                OfferProposalStatus.NEW.value,
                OfferProposalStatus.ACTIVE_READ.value])

            application_tasks = MyActivity.my_applications(tx, user, [
                ApplicationStatus.SELECTED.value])
            proposal_tasks = MyActivity.my_proposals(tx, user, [
                OfferProposalStatus.SELECTED.value,
                OfferProposalStatus.IN_PROGRESS.value,
                OfferProposalStatus.COMPLETED.value])

            my_communities = MyActivity.my_communities(tx, user)
            my_events = MyActivity.my_events(tx, user)
            my_connections = MyActivity.my_connections(tx, user)

            bookmarked_users = User.my_bookmarks(tx, user)
            bookmarked_gigs = Post.my_bookmarks(tx, user)
            bookmarked_offers = Offer.my_bookmarks(tx, user)
            bookmarked_positions = Position.my_bookmarks(tx, user)
            bookmarked_communities = Community.my_bookmarks(tx, user)
            bookmarked_events = Event.my_bookmarks(tx, user)

            # TODO: (santanu) Move this to a activities(Model) dict
            activities = {
                'posts': {
                    'gigs': [gig.as_dict() for gig in own_gigs],
                    'offers': [offer.as_dict() for offer in own_offers],
                    'positions': [position.as_dict() for position in own_positions]
                },
                'applications': {
                    'applications': [applications.as_dict() for applications in my_applications],
                    'proposals': [proposal.as_dict() for proposal in my_proposals]
                },
                'tasks': {
                    'applications': [application.as_dict() for application in application_tasks],
                    'proposals': [proposal.as_dict() for proposal in proposal_tasks]
                },
                'communities': [community.as_dict() for community in my_communities],
                'events': [event.as_dict() for event in my_events],
                'connections': [connection.as_dict() for connection in my_connections],
                'bookmarks': {
                    'peoples': [user.as_summary_dict() for user in bookmarked_users],
                    'gigs': [gig.as_dict(user=user) for gig in bookmarked_gigs],
                    'offers': [offer.as_dict() for offer in bookmarked_offers],
                    'positions': [position.as_dict() for position in bookmarked_positions],
                    'community': [community.as_dict() for community in bookmarked_communities],
                    'events': [event.as_dict() for event in bookmarked_events],
                }
            }

        return jsonify(activities)
