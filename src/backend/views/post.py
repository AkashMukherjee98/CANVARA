from datetime import datetime
import uuid

from flask import current_app as app
from flask import jsonify, request
from flask_cognito import cognito_auth_required, current_cognito_jwt

from backend.common.exceptions import InvalidArgumentError, NotAllowedError
from backend.models.db import transaction
from backend.models.location import Location
from backend.models.post import Post
from backend.models.post_type import PostType
from backend.models.user import User


@app.route('/posts', methods=['POST'])
@cognito_auth_required
def create_post_handler():
    payload = request.json

    # TODO: (sunil) Need a better way to validate the request
    required_fields = {'language', 'location_id', 'name', 'people_needed', 'post_type_id', 'size', 'target_date'}
    missing_fields = required_fields - set(payload.keys())
    if missing_fields:
        raise InvalidArgumentError(f"Invalid request: {', '.join(missing_fields)} missing")

    # target_date must be in ISO 8601 format (YYYY-MM-DD)
    try:
        target_date = datetime.fromisoformat(payload['target_date']).date()
        # target_date = target_date.date().isoformat()
    except ValueError as ex:
        raise InvalidArgumentError(f"Unable to parse target_date: {payload['target_date']}") from ex

    Post.validate_size(payload['size'])

    # Generate a unique id for this post
    post_id = str(uuid.uuid4())

    now = datetime.utcnow()
    with transaction() as tx:
        owner = User.lookup(tx, current_cognito_jwt['sub'])
        post_type = PostType.lookup(tx, payload['post_type_id'])
        location = Location.lookup(tx, payload['location_id'])
        post = Post(
            id=post_id,
            owner=owner,
            created_at=now,
            last_updated_at=now,
            name=payload['name'],
            post_type=post_type,
            description=payload.get('description'),
            size=payload['size'].upper(),
            language=payload['language'],
            location=location,
            people_needed=payload['people_needed'],
            target_date=target_date
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
        payload = request.json
        user = User.lookup(tx, current_cognito_jwt['sub'])
        post = Post.lookup(tx, post_id)

        # For now, only the post owner is allowed to update the post
        if post.owner_id != user.id:
            raise NotAllowedError(f"User '{user.id}' is not the post owner")

        # If target_date was specified, it must be in ISO 8601 format (YYYY-MM-DD)
        if 'target_date' in payload:
            try:
                post.target_date = datetime.fromisoformat(payload['target_date']).date()
            except ValueError as ex:
                raise InvalidArgumentError(f"Unable to parse target_date: {payload['target_date']}") from ex

        if 'post_type_id' in payload:
            post.post_type = PostType.lookup(tx, payload['post_type_id'])

        if 'location_id' in payload:
            post.location = PostType.lookup(tx, payload['location_id'])

        if 'size' in payload:
            Post.validate_size(payload['size'])
            post.size = payload['size'].upper()

        settables = ['description', 'language', 'name', 'people_needed']
        for field in settables:
            if field in payload:
                setattr(post, field, payload[field])

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
