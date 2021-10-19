from datetime import datetime
from functools import partial
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt

from backend.common.exceptions import InvalidArgumentError, NotAllowedError
from backend.common.http import make_no_content_response
from backend.models.db import transaction
from backend.models.language import Language
from backend.models.location import Location
from backend.models.post import Post, PostFilter, PostStatus, UserPostBookmark, UserPostLike
from backend.models.post_type import PostType
from backend.models.user import User
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase


class PostAPI(AuthenticatedAPIBase):
    @staticmethod
    def __list_posts():
        post_filter = PostFilter.lookup(request.args.get('filter'))

        with transaction() as tx:
            # This is the user making the request, for authorization purposes
            user = User.lookup(tx, current_cognito_jwt['sub'])
            posts = Post.search(
                tx,
                user,
                owner_id=request.args.get('post_owner_id'),
                query=request.args.get('q'),
                post_type_id=request.args.get('type'),
                post_filter=post_filter
            )
            posts = [post.as_dict(user=user) for post in posts]
        return jsonify(posts)

    @staticmethod
    def __get_post(post_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, post_id)
            return post.as_dict(user=user)

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
        language = Language.validate_and_convert_language(payload['language'])

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
            name = payload['name']
            summary = payload['summary']
            post = Post(
                id=post_id,
                owner=owner,
                created_at=now,
                last_updated_at=now,
                post_type=post_type,
                status=Post.DEFAULT_INITIAL_POST_STATUS.value,
                description=payload.get('description'),
                size=size,
                language=language,
                location=location,
                people_needed=payload['people_needed'],
                candidate_description=payload.get('candidate_description'),
                target_date=target_date,
                expiration_date=expiration_date
            )
            if name.length > 48:
                raise InvalidArgumentError("Invalid Entry: Name must be less than 48 characters.")
            if summary.length > 144:
                raise InvalidArgumentError("Invalid Entry: Summary must be less than 144 characters.")
            if payload.get('required_skills'):
                Post.validate_required_skills(payload['required_skills'])
                post.set_required_skills(tx, payload['required_skills'])
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
                post.location = Location.lookup(tx, payload['location_id'])

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
                    'validate_and_convert': Language.validate_and_convert_language
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
            post = Post.lookup(tx, post_id)

            # For now, only the post owner is allowed to delete the post
            if post.owner_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the post owner")
            post.status = PostStatus.DELETED.value
        return make_no_content_response()

    @staticmethod
    def saveDraft(post_id):
        with transaction() as tx:
            post = Post.lookup(tx, post_id)
            post.status = PostStatus.SAVED.value
        return make_no_content_response()


class PostVideoAPI(AuthenticatedAPIBase, UserUploadMixin):

    @staticmethod
    def put(post_id):
        # TODO: (sunil) add validation for accepted content types
        metadata = {
            'resource': 'post',
            'resource_id': post_id,
            'type': 'video',
        }
        return PostVideoAPI.create_user_upload(
            current_cognito_jwt['sub'], request.json['filename'], request.json['content_type'], 'posts', metadata)


class PostVideoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(post_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            post = Post.lookup(tx, post_id)
            if status == UserUploadStatus.UPLOADED:
                post.description_video = user_upload
                user_upload.status = status.value
            # TODO: (sunil) return an error if this status transition is not supported

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(post_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            post = Post.lookup(tx, post_id)

            # For now, only the post owner is allowed to delete the post video
            if post.owner_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the post owner")
            post.description_video = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()

    @staticmethod
    def saveDraft(post_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            post = Post.lookup(tx, post_id)
            post.description_video = None
            user_upload.status = UserUploadStatus.SAVED.value
        return make_no_content_response()


class PostBookmarkAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(post_id):
        with transaction() as tx:
            post = Post.lookup(tx, post_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])

            # noop if the bookmark already exists, otherwise add one
            # TODO: (sunil) may need to acquire a mutex to handle concurrent requests
            bookmark = UserPostBookmark.lookup(tx, user.id, post.id, must_exist=False)
            if bookmark is None:
                UserPostBookmark(user=user, post=post, created_at=datetime.utcnow())
        return make_no_content_response()

    @staticmethod
    def delete(post_id):
        with transaction() as tx:
            post = Post.lookup(tx, post_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])
            bookmark = UserPostBookmark.lookup(tx, user.id, post.id)
            tx.delete(bookmark)
        return make_no_content_response()

    @staticmethod
    def saveDraft(post_id):
        with transaction() as tx:
            post = Post.lookup(tx, post_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])
            bookmark = UserPostBookmark.lookup(tx, user.id, post.id)
            tx.save(bookmark)
        return make_no_content_response()


class PostLikeAPI(AuthenticatedAPIBase):

    @staticmethod
    def put(post_id):
        with transaction() as tx:
            post = Post.lookup(tx, post_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])

            # noop if the like already exists, otherwise add one
            # TODO: (sunil) may need to acquire a mutex to handle concurrent requests
            like = UserPostLike.lookup(tx, user.id, post.id, must_exist=False)
            if like is None:
                UserPostLike(user=user, post=post, created_at=datetime.utcnow())
        return make_no_content_response()

    @staticmethod
    def delete(post_id):
        with transaction() as tx:
            post = Post.lookup(tx, post_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])
            like = UserPostLike.lookup(tx, user.id, post.id)
            tx.delete(like)
        return make_no_content_response()

    @staticmethod
    def saveDraft(post_id):
        with transaction() as tx:
            post = Post.lookup(tx, post_id)
            user = User.lookup(tx, current_cognito_jwt['sub'])
            like = UserPostLike.lookup(tx, user.id, post.id)
            tx.save(like)
        return make_no_content_response()


class PostTypeAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            query = tx.query(PostType)
            return jsonify([post_type.as_dict() for post_type in query])


class LocationAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            query = tx.query(Location).with_parent(user.customer)
            return jsonify([location.as_dict() for location in query])


class LanguageAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        return jsonify(Language.SUPPORTED_LANGUAGES)
