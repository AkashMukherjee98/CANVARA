from datetime import datetime
import copy
import uuid

from flask import jsonify, request
from flask_cognito import cognito_auth_required, current_cognito_jwt

from common.exceptions import InvalidArgumentError, NotAllowedError
from models.db import transaction
from models.post import Post
from models.user import User
from app import app

@app.route('/posts', methods=['POST'])
@cognito_auth_required
def create_post_handler():
    payload = request.json
    details = {}

    # If target_date was specified, it must be in ISO 8601 format (YYYY-MM-DD)
    if payload.get('target_date'):
        try:
            target_date = datetime.fromisoformat(payload['target_date'])
            details['target_date'] = target_date.date().isoformat()
        except ValueError:
            raise InvalidArgumentError(f"Unable to parse target_date: {payload['target_date']}")

    if payload.get('summary'):
        details['summary'] = payload['summary']

    if payload.get('description'):
        details['description'] = payload['description']

    if payload.get('size'):
        details['size'] = payload['size']

    # Generate a unique id for this post
    post_id = str(uuid.uuid4())

    now = datetime.utcnow()
    with transaction() as tx:
        owner = User.lookup(tx, current_cognito_jwt['sub'])
        post = Post(
            id=post_id,
            owner=owner,
            created_at=now,
            last_updated_at=now,
            details=details
        )
    return post.as_dict()

@app.route('/posts')
@cognito_auth_required
def list_posts_handler():
    with transaction() as tx:
        # This is the user making the request, for authorization purposes
        user = User.lookup(tx, current_cognito_jwt['sub'])
        posts = Post.search(
            tx,
            user.customer_id,
            owner_id=request.args.get('post_owner_id'),
            query=request.args.get('q')
        )
    return jsonify(posts)

@app.route('/posts/<post_id>')
@cognito_auth_required
def get_post_handler(post_id):
    with transaction() as tx:
        post = Post.lookup(tx, post_id)
    return post.as_dict()

@app.route('/posts/<post_id>', methods=['PUT'])
@cognito_auth_required
def update_post_handler(post_id):
    with transaction() as tx:
        user = User.lookup(tx, current_cognito_jwt['sub'])
        post = Post.lookup(tx, post_id)

        # For now, only the post owner is allowed to update the post
        if post.owner_id != user.id:
            raise NotAllowedError(f"User '{user.id}' is not the post owner")

        payload = request.json
        details = copy.deepcopy(post.details)

        # If target_date was specified, it must be in ISO 8601 format (YYYY-MM-DD)
        if 'target_date' in payload:
            try:
                target_date = datetime.fromisoformat(payload['target_date'])
                details['target_date'] = target_date.date().isoformat()
            except ValueError:
                raise InvalidArgumentError(f"Unable to parse target_date: {payload['target_date']}")

        if 'size' in payload:
            details['size'] = payload['size']

        if 'summary' in payload:
            details['summary'] = payload['summary']

        if 'description' in payload:
            details['description'] = payload['description']

        post.details = details
        post.last_updated_at = datetime.utcnow()
    return post.as_dict()

@app.route('/posts/<post_id>', methods=['DELETE'])
@cognito_auth_required
def delete_post_handler(post_id):
    with transaction() as tx:
        user = User.lookup(tx, current_cognito_jwt['sub'])
        post = Post.lookup(tx, post_id, must_exist=False)

        if post is None:
            # Noop if the post does not exist
            return {}

        # For now, only the post owner is allowed to delete the post
        if post.owner_id != user.id:
            raise NotAllowedError(f"User '{user.id}' is not the post owner")
        tx.delete(post)
    return {}
