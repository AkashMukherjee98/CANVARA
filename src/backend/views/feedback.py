from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.exceptions import NotAllowedError
from backend.models.db import transaction
from backend.models.feedback import Feedback, FeedbackUserRole
from backend.models.performer import Performer
from backend.models.post import Post
from backend.models.user import User
from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('feedback', __name__, url_prefix='/posts/<post_id>')


@blueprint.route('/performers/<performer_id>/feedback')
class PerformerFeedbackAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id, performer_id):
        with transaction() as tx:
            # This API can be called only by the post owner
            user = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, post_id)
            if user.id != post.owner.id:
                raise NotAllowedError(f"Only post owner can see performer feedback. User '{user.id}' is not the post owner.")
            feedback = Feedback.lookup_by_performer(tx, post_id, performer_id)
        return feedback.as_dict()

    @staticmethod
    def post(post_id, performer_id):
        with transaction() as tx:
            author = User.lookup(tx, current_cognito_jwt['sub'])
            performer = User.lookup(tx, performer_id)
            post = Post.lookup(tx, post_id)

            # This API can be called only by the post owner
            if author.id != post.owner.id:
                raise NotAllowedError(f"Only post owner can submit performer feedback. "
                                      f"User '{author.id}' is not the post owner.")

            if Performer.lookup(tx, post_id, performer.id, must_exist=False) is None:
                raise NotAllowedError(f"User '{performer.id}' is not a performer for post '{post.id}'.")

            # TODO: (sunil) add check for performer status

            payload = request.json
            feedback_details = {}
            if 'comments' in payload:
                feedback_details['comments'] = payload['comments']

            if 'concerns' in payload:
                feedback_details['concerns'] = payload['concerns']

            if 'additional_comments' in payload:
                feedback_details['additional_comments'] = payload['additional_comments']

            if 'is_hidden' in payload:
                feedback_details['is_hidden'] = payload['is_hidden']

            feedback = Feedback(
                id=str(uuid.uuid4()),
                author=author,
                post=post,
                user=performer,
                user_role=FeedbackUserRole.PERFORMER.value,
                feedback=feedback_details,
                created_at=datetime.utcnow(),
            )
            tx.add(feedback)
        return feedback.as_dict()

    @staticmethod
    def put(post_id, performer_id):
        now = datetime.utcnow()

        with transaction() as tx:
            author = User.lookup(tx, current_cognito_jwt['sub'])
            performer = User.lookup(tx, performer_id)
            post = Post.lookup(tx, post_id)
            feedback = Feedback.lookup_by_feedback(tx, author.id, post.id, performer.id)

            payload = request.json

            feedback.last_updated_at = now
            feedback.update_feedback(payload)

        # Fetch the feedback again from the database so the updates made above are reflected in the response
        with transaction() as tx:
            feedback = Feedback.lookup_by_feedback(tx, author.id, post.id, performer.id)
            feedback_details = feedback.as_dict()
        return feedback_details


@blueprint.route('/feedback')
class PosterFeedbackAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id):
        with transaction() as tx:
            feedback = Feedback.lookup_by_post(tx, post_id)
        return jsonify([item.as_dict() for item in feedback])

    @staticmethod
    def post(post_id):
        with transaction() as tx:
            author = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, post_id)

            # This API can be called only by a post performer
            if Performer.lookup(tx, post_id, author.id, must_exist=False) is None:
                raise NotAllowedError(f"Only post performer can submit feedback for post owner. "
                                      f"User '{author.id}' is not a performer for post '{post.id}'.")

            # TODO: (sunil) add check for performer status

            payload = request.json
            feedback_details = {}
            if 'comments' in payload:
                feedback_details['comments'] = payload['comments']

            if 'concerns' in payload:
                feedback_details['concerns'] = payload['concerns']

            if 'additional_comments' in payload:
                feedback_details['additional_comments'] = payload['additional_comments']

            if 'is_hidden' in payload:
                feedback_details['is_hidden'] = payload['is_hidden']

            feedback = Feedback(
                id=str(uuid.uuid4()),
                author=author,
                post=post,
                user=post.owner,
                user_role=FeedbackUserRole.POSTER.value,
                feedback=feedback_details,
                created_at=datetime.utcnow(),
            )
            tx.add(feedback)
        return feedback.as_dict()

    @staticmethod
    def put(post_id):
        now = datetime.utcnow()

        with transaction() as tx:
            author = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, post_id)
            feedback = Feedback.lookup_by_feedback(tx, author.id, post.id, post.owner.id)

            payload = request.json

            feedback.last_updated_at = now
            feedback.update_feedback(payload)

        # Fetch the feedback again from the database so the updates made above are reflected in the response
        with transaction() as tx:
            feedback = Feedback.lookup_by_feedback(tx, author.id, post.id, post.owner.id)
            feedback_details = feedback.as_dict()
        return feedback_details
