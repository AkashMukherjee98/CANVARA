from datetime import datetime
from functools import partial
import uuid

from flask import jsonify, request
from flask.views import MethodView
from flask_cognito import current_cognito_jwt

from backend.common.exceptions import InvalidArgumentError, NotAllowedError
from backend.models.db import transaction
from backend.models.language import Language
from backend.models.location import Location
from backend.models.post import Post
from backend.models.post_type import PostType
from backend.models.user import User


class PostAPI(MethodView):
    @staticmethod
    def __list_posts():
        # TODO: (sunil) Use filter arg to filter the query results
        # filter = request.args.get('filter', 'curated').lower()

        with transaction() as tx:
            # This is the user making the request, for authorization purposes
            user = User.lookup(tx, current_cognito_jwt['sub'])
            posts = Post.search(
                tx,
                user.customer_id,
                owner_id=request.args.get('post_owner_id'),
                query=request.args.get('q'),
                post_type_id=request.args.get('type')
            )
        return jsonify(posts)

    @staticmethod
    def __get_post(post_id):
        with transaction() as tx:
            post = Post.lookup(tx, post_id)
            return post.as_dict()

    @staticmethod
    def get(post_id=None):
        if post_id is None:
            return PostAPI.__list_posts()
        return PostAPI.__get_post(post_id)

    @staticmethod
    def post():
        payload = request.json

        # TODO: (sunil) Need a better way to validate the request
        required_fields = {'language', 'location_id', 'name', 'people_needed', 'post_type_id', 'size', 'target_date'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Invalid request: {', '.join(missing_fields)} missing")

        target_date = Post.validate_and_convert_target_date(payload['target_date'])
        size = Post.validate_and_convert_size(payload['size'])
        language = Post.validate_and_convert_language(payload['language'])

        if payload.get('expiration_date'):
            expiration_date = Post.validate_and_convert_expiration_date(payload['expiration_date'])
        else:
            expiration_date = None

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
                status=Post.DEFAULT_INITIAL_POST_STATUS.value,
                description=payload.get('description'),
                video_url=Post.DEFAULT_VIDEO_URL,  # TODO: (sunil) Remove this once video upload is supported
                size=size,
                language=language,
                location=location,
                people_needed=payload['people_needed'],
                candidate_description=payload.get('candidate_description'),
                target_date=target_date,
                expiration_date=expiration_date
            )

            if payload.get('required_skills'):
                Post.validate_required_skills(payload['required_skills'])
                post.set_required_skills(tx, payload['required_skills'])

            if payload.get('desired_skills'):
                Post.validate_desired_skills(payload['desired_skills'])
                post.set_desired_skills(tx, payload['desired_skills'])
            return post.as_dict()

    @staticmethod
    def put(post_id):
        with transaction() as tx:
            payload = request.json
            user = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, post_id)

            # For now, only the post owner is allowed to update the post
            if post.owner_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the post owner")

            if 'post_type_id' in payload:
                post.post_type = PostType.lookup(tx, payload['post_type_id'])

            if 'location_id' in payload:
                post.location = PostType.lookup(tx, payload['location_id'])

            # TODO: (sunil) Move this to the Post model
            settables = {
                'candidate_description': {},
                'description': {},
                'desired_skills': {
                    'validate_and_convert': Post.validate_desired_skills,
                    'setter': partial(post.set_desired_skills, tx)
                },
                'expiration_date': {
                    'validate_and_convert': Post.validate_and_convert_expiration_date
                },
                'language': {
                    'validate_and_convert': Post.validate_and_convert_language
                },
                'name': {},
                'people_needed': {},
                'required_skills': {
                    'validate_and_convert': Post.validate_required_skills,
                    'setter': partial(post.set_required_skills, tx)
                },
                'size': {
                    'validate_and_convert': Post.validate_and_convert_size
                },
                'status': {
                    'validate_and_convert': Post.validate_and_convert_status
                },
                'target_date': {
                    'validate_and_convert': Post.validate_and_convert_target_date
                }
            }

            for field in settables:
                if field in payload:
                    value = payload[field]
                    if settables[field].get('validate_and_convert'):
                        value = settables[field]['validate_and_convert'](value)

                    if settables[field].get('setter'):
                        settables[field]['setter'](value)
                    else:
                        setattr(post, field, value)

            post.last_updated_at = datetime.utcnow()

        # Fetch the post again from the database so the updates made above are reflected in the response
        with transaction() as tx:
            post = Post.lookup(tx, post_id)
            return post.as_dict()

    @staticmethod
    def delete(post_id):
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


class PostTypeAPI(MethodView):
    @staticmethod
    def get():
        with transaction() as tx:
            query = tx.query(PostType)
            return jsonify([post_type.as_dict() for post_type in query])


class LocationAPI(MethodView):
    @staticmethod
    def get():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            query = tx.query(Location).with_parent(user.customer)
            return jsonify([location.as_dict() for location in query])


class LanguageAPI(MethodView):
    @staticmethod
    def get():
        return jsonify(Language.SUPPORTED_LANGUAGES)
