from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint
import sqlalchemy.exc

from backend.common.exceptions import InvalidArgumentError
from backend.common.http import make_no_content_response
from backend.models.db import transaction
from backend.models.match import UserPostMatch
from backend.models.post import Post
from backend.models.user import User
from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('match', __name__, url_prefix='/matches')


@blueprint.route('')
class MatchAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        user_id = request.args.get('user_id')
        post_id = request.args.get('post_id')
        with transaction() as tx:
            matches = UserPostMatch.lookup_multiple(tx, user_id=user_id, post_id=post_id)
            return jsonify([match.as_dict() for match in matches])

    @staticmethod
    def post():
        payload = request.json
        user_id = payload['user_id']
        post_id = payload['post_id']

        now = datetime.utcnow()
        try:
            with transaction() as tx:
                matcher = User.lookup(tx, current_cognito_jwt['sub'])
                user = User.lookup(tx, user_id)
                post = Post.lookup(tx, post_id)

                match = UserPostMatch(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    post_id=post.id,
                    confidence_level=payload['match_level'],
                    created_at=now,
                    updated_at=now,
                    updated_by=str(matcher.id)
                )
                tx.add(match)
                return match.as_dict()
        except sqlalchemy.exc.IntegrityError as ex:
            raise InvalidArgumentError(f"Match already exists for user '{user_id}' and post '{post_id}'") from ex


@blueprint.route('/<match_id>')
class MatchByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(match_id):
        with transaction() as tx:
            return UserPostMatch.lookup(tx, match_id).as_dict()

    @staticmethod
    def put(match_id):
        with transaction() as tx:
            match = UserPostMatch.lookup(tx, match_id)
            matcher = User.lookup(tx, current_cognito_jwt['sub'])

            match.confidence_level = request.json['match_level']
            match.updated_at = datetime.utcnow()
            match.updated_by = str(matcher.id)
            return match.as_dict()

    @staticmethod
    def delete(match_id):
        with transaction() as tx:
            match = UserPostMatch.lookup(tx, match_id)
            tx.delete(match)
        return make_no_content_response()
