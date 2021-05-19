from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import cognito_auth_required, current_cognito_jwt

from common.exceptions import DoesNotExistError, InvalidArgumentError, NotAllowedError
from models.post import Post
from models.user import User
from app import app

@app.route('/posts', methods=['POST'])
@cognito_auth_required
def create_post_handler():
    post_owner = User.lookup(current_cognito_jwt['sub'])
    payload = request.json

    # Validate the task_owner_id, if it was specified
    task_owner_id = payload.get('task_owner_id', post_owner.user_id)
    if task_owner_id != post_owner.user_id and not User.exists(task_owner_id):
        raise DoesNotExistError(f"User '{task_owner_id}' does not exist")

    post_details = {}

    # If target_date was specified, it must be in ISO 8601 format (YYYY-MM-DD)
    if payload.get('target_date'):
        try:
            target_date = datetime.fromisoformat(payload['target_date'])
            post_details['target_date'] = target_date.date().isoformat()
        except ValueError:
            raise InvalidArgumentError(f"Unable to parse target_date: {payload['target_date']}")

    if payload.get('size'):
        post_details['size'] = payload['size']

    # Generate a unique id for this post
    post_id = str(uuid.uuid4())

    now = datetime.utcnow().isoformat()
    post = Post(
        post_owner.customer_id,
        post_id,
        post_owner_id=post_owner.user_id,
        task_owner_id=task_owner_id,
        summary=payload['summary'],
        description=payload['description'],
        created_at=now,
        last_updated_at=now,
        details=post_details
    )
    post.save()
    return post.as_dict()

@app.route('/posts')
@cognito_auth_required
def list_posts_handler():
    # This is the user making the request, for authorization purposes
    user = User.lookup(current_cognito_jwt['sub'])
    posts = Post.search(
        user.customer_id,
        post_owner_id=request.args.get('post_owner_id'),
        task_owner_id=request.args.get('task_owner_id'),
        query=request.args.get('q')
        )
    return jsonify(posts)

@app.route('/posts/<post_id>')
@cognito_auth_required
def get_post_handler(post_id):
    user = User.lookup(current_cognito_jwt['sub'])
    post = Post.lookup(user.customer_id, post_id)
    return post.as_dict()

@app.route('/posts/<post_id>', methods=['PUT'])
@cognito_auth_required
def update_post_handler(post_id):
    user = User.lookup(current_cognito_jwt['sub'])
    post = Post.lookup(user.customer_id, post_id)

    # For now, only the post owner is allowed to update the post
    if post.post_owner_id != user.user_id:
        raise NotAllowedError(f"User '{user.user_id}' is not the post owner")

    payload = request.json
    # Validate the task_owner_id, if it was specified
    task_owner_id = payload.get('task_owner_id', post.task_owner_id)
    if task_owner_id != post.task_owner_id and not User.exists(task_owner_id):
        raise DoesNotExistError(f"User '{task_owner_id}' does not exist")

    # If target_date was specified, it must be in ISO 8601 format (YYYY-MM-DD)
    if payload.get('target_date'):
        try:
            target_date = datetime.fromisoformat(payload['target_date'])
            post.details.target_date = target_date.date().isoformat()
        except ValueError:
            raise InvalidArgumentError(f"Unable to parse target_date: {payload['target_date']}")

    if payload.get('size'):
        post.details.size = payload['size']

    post.task_owner_id = task_owner_id
    post.summary = payload.get('summary', post.summary)
    post.description = payload.get('description', post.description)
    post.last_updated_at = datetime.utcnow().isoformat()
    post.save()
    return post.as_dict()

@app.route('/posts/<post_id>', methods=['DELETE'])
@cognito_auth_required
def delete_post_handler(post_id):
    user = User.lookup(current_cognito_jwt['sub'])
    post = Post.lookup(user.customer_id, post_id, must_exist=False)

    if post is None:
        # Noop if the post does not exist
        return

    # For now, only the post owner is allowed to delete the post
    if post.post_owner_id != user.user_id:
        raise NotAllowedError(f"User '{user.user_id}' is not the post owner")

    post.delete()
    return {}
