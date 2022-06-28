import json

from flask import request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint
from backend.models.slack import send_slack_notification, slack_notification_response, validate_slack_details, \
    check_slack_details
from backend.models.db import transaction
from backend.models.user import User
from backend.views.base import AuthenticatedAPIBase

blueprint = Blueprint('slack', __name__, url_prefix='/slack')


@blueprint.route('/user')
class SlackUpdateAPI(AuthenticatedAPIBase):

    @staticmethod
    def put():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            payload = request.json

            if payload.get('slack_id'):
                user.slack_id = payload['slack_id']
            if payload.get('workspace_id'):
                user.workspace_id = payload['workspace_id']
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            send_slack_notification(user, "Welcome to Canvara!!!")
        return check_slack_details(user, payload['slack_id'], payload['workspace_id'])


@blueprint.route('/notification')
class SlackSendNotificationAPI(AuthenticatedAPIBase):

    @staticmethod
    def post():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            validate_slack_details(user)

            payload = request.json

            if 'text' in payload:
                text = payload["text"]

        response = send_slack_notification(user, text)
        return slack_notification_response(json.loads(response.text))
