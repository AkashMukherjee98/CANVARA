from flask import jsonify
from flask import request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.views.base import AuthenticatedAPIBase
from backend.models.db import transaction
from backend.models.user import User
from backend.models.application import ApplicationStatus
from backend.models.offer import OfferProposalStatus

from backend.models.activities import Activity, ActivityGlobal
from backend.models.activities import MyActivity


blueprint = Blueprint('activities', __name__, url_prefix='/activities')
blueprint_myactivities = Blueprint('myactivities', __name__, url_prefix='/myactivities')


@blueprint.route('/my')
class ActivityAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        start = int(request.args.get('start')) if request.args.get('start') is not None else None
        limit = int(request.args.get('limit')) if request.args.get('limit') is not None else None

        user_id = current_cognito_jwt['sub']
        with transaction() as tx:
            activities = Activity.find_multiple(tx, user_id, start=start, limit=limit)

            return {
                'activities': [activitiy.as_dict() for activitiy in activities],
                'total_unread': Activity.unread_count(tx, user_id),
            }


@blueprint.route('/global')
class ActivityGlobalAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        start = int(request.args.get('start')) if request.args.get('start') is not None else None
        limit = int(request.args.get('limit')) if request.args.get('limit') is not None else None

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            activities = ActivityGlobal.find_multiple(tx, user.customer_id, start=start, limit=limit)

            return {
                'activities': [activitiy.as_dict() for activitiy in activities]
            }


# Old my activities code starts here - DEPRICATED
@blueprint_myactivities.route('')
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

            bookmarked_users = []
            bookmarked_gigs = []
            bookmarked_offers = []
            bookmarked_positions = []
            bookmarked_communities = []
            bookmarked_events = []

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
                    'events': [event.as_dict() for event in bookmarked_events]
                }
            }

        return jsonify(activities)


@blueprint_myactivities.route('/count')
class MyActivityCountAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():  # pylint: disable=too-many-locals
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            overall_count = MyActivity.activities_count(tx, user)
            return jsonify(overall_count)


@blueprint_myactivities.route('/one')
class MyActivityOneAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():  # pylint: disable=too-many-locals
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            overall_snaps = MyActivity.activities_one(tx, user)
            return jsonify(overall_snaps)
