from datetime import datetime
import uuid

from flask import request, jsonify
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.exceptions import InvalidArgumentError, NotAllowedError, DoesNotExistError
from backend.common.http import make_no_content_response
from backend.models.db import transaction
from backend.models.user import User
from backend.models.post import Post
from backend.models.share import Share
from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('share', __name__, url_prefix='/shares')


@blueprint.route('')
class EventAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            # This is the user making the request, for authorization purposes
            user = User.lookup(tx, current_cognito_jwt['sub'])
            
            events = Share.search(
                tx,
                user
            )
            events = [event.as_dict() for event in events]
        return jsonify(events)

    @staticmethod
    def post():
        payload = request.json
        share_id = str(uuid.uuid4())
        now = datetime.utcnow()

        required_fields = {'share_with_user_id', 'share_item_id'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Parameter: {', '.join(missing_fields)} is required")

        with transaction() as tx:
            shared_by = User.lookup(tx, current_cognito_jwt['sub'])
            shared_with = User.lookup(tx, payload['share_with_user_id'])
            item = Post.lookup(tx, payload['share_item_id'])

            share = Share(
                id=share_id,
                shared_by=shared_by,
                shared_with=shared_with,
                item=item,
                item_type="gig",
                notes=payload['notes'],
                created_at=now
            )
            tx.add(share)

            share_details = share.as_dict()
        return share_details


@blueprint.route('/<share_id>')
class EventByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def delete(event_id):
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            event = Share.lookup(tx, event_id)

            # For now, only owner can delete his shared item
            if event.primary_organizer_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not a primary organizer of the event.")
            event.last_updated_at = now
        return make_no_content_response()