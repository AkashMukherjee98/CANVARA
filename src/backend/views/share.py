from datetime import datetime
import uuid

from flask import request, jsonify
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.exceptions import InvalidArgumentError
from backend.models.db import transaction
from backend.models.user import User
from backend.models.post import Post
from backend.models.offer import Offer
from backend.models.position import Position
from backend.models.event import Event
from backend.models.community import Community
from backend.models.share import Share, ShareItemType
from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('share', __name__, url_prefix='/shares')


@blueprint.route('')
class EventAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        payload = request.json
        share_id = str(uuid.uuid4())
        now = datetime.utcnow()

        required_fields = {'share_with_user_ids', 'item_type', 'item_id'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Parameter: {', '.join(missing_fields)} is required.")

        if not isinstance(payload['share_with_user_ids'], list):
            raise InvalidArgumentError("Share with users should be a list of user id.")

        item_type = ShareItemType.validate_and_return_item_type(payload['item_type'])

        with transaction() as tx:
            share_by = User.lookup(tx, current_cognito_jwt['sub'])

            share_with_user_ids = []
            for share_with_user_id in payload['share_with_user_ids']:
                user = User.lookup(tx, share_with_user_id)
                share_with_user_ids.append(user.id)

            item = None
            if item_type == 'gig':
                item = Post.lookup(tx, payload['item_id'])
            elif item_type == 'offer':
                item = Offer.lookup(tx, payload['item_id'])
            elif item_type == 'position':
                item = Position.lookup(tx, payload['item_id'])
            elif item_type == 'event':
                item = Event.lookup(tx, payload['item_id'])
            elif item_type == 'community':
                item = Community.lookup(tx, payload['item_id'])
            elif item_type == 'people':
                item = User.lookup(tx, payload['item_id'])

            share = Share(
                id=share_id,
                share_by=share_by,
                share_with_user_ids=share_with_user_ids,
                item_type=item_type,
                item_id=item.id,
                message=payload['message'] if payload.get('message') else None,
                created_at=now
            )
            tx.add(share)

            share_details = share.as_dict()
        return share_details

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
