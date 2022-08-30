# NEW CODE

from datetime import datetime
from functools import partial
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint
from backend.common.exceptions import InvalidArgumentError, NotAllowedError
from backend.common.http import make_no_content_response
from backend.models.db import transaction
from backend.models.language import Language
from backend.models.location import Location
from backend.models.skill import Skill
from backend.models.post import Post, PostSort, PostStatusFilter, PostFilter, PostStatus, UserPostBookmark, UserPostLike
from backend.models.post_type import PostType
from backend.models.user import User
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase
from backend.common.permission import Permissions
from backend.models.activities import Activity, ActivityGlobal, ActivityType


blueprint = Blueprint('post', __name__, url_prefix='/posts')
post_type_blueprint = Blueprint('post_type', __name__, url_prefix='/post_types')
location_blueprint = Blueprint('location', __name__, url_prefix='/locations')
language_blueprint = Blueprint('language', __name__, url_prefix='/languages')


@blueprint.route('')
class PostAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        post_filter = PostFilter.lookup(request.args.get('filter'))

        sort = PostSort.lookup(request.args.get('sort'))
        keyword = request.args.get('keyword')
        status = PostStatusFilter.lookup(request.args.get('status'))

        project_size = Post.validate_and_convert_size(
            request.args.get('project_size')) if 'project_size' in request.args else None
        target_date = Post.validate_and_convert_target_date(
            request.args.get('target_date')) if 'target_date' in request.args else None
        department = request.args.get('department') if 'department' in request.args else None

        with transaction() as tx:
            # This is the user making the request, for authorization purposes
            user = User.lookup(tx, current_cognito_jwt['sub'])
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['readPermission'] == 'Yes':
                    location = Location.lookup(tx, request.args.get(
                        'location_id')) if 'location_id' in request.args else None

                    skill = Skill.lookup(tx, user.customer_id,
                                         request.args.get('skill_id')) if 'skill_id' in request.args else None

                    posts = Post.search(
                        tx,
                        user,
                        # Old & deprecated params
                        owner_id=request.args.get('post_owner_id'),
                        query=request.args.get('q'),
                        post_type_id=request.args.get('type'),
                        post_filter=post_filter,
                        # New & updated params
                        sort=sort,
                        keyword=keyword,
                        status=status,
                        project_size=project_size,
                        target_date=target_date,
                        location=location,
                        department=department,
                        skill=skill
                    )
                    posts = [post.as_dict(user=user) for post in posts]
                    return jsonify(posts)
            raise NotAllowedError(f"User '{user.id}' has no permission to see gig")

    @staticmethod
    def post():  # pylint: disable=too-many-locals
        payload = request.json

        # TODO: (sunil) Need a better way to validate the request
        required_fields = {'language', 'location_id', 'name', 'people_needed', 'post_type_id', 'size', 'target_date'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Invalid request: {', '.join(missing_fields)} missing")

        name = Post.validate_and_convert_name(payload['name'])
        description = Post.validate_and_convert_description(payload['description'])
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
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['createPermission'] == 'Yes':
                    department = owner.profile['department'] if 'department' in owner.profile else None
                    post_type = PostType.lookup(tx, payload['post_type_id'])
                    location = Location.lookup(tx, payload['location_id'])
                    post = Post(
                        id=post_id,
                        owner=owner,
                        created_at=now,
                        last_updated_at=now,
                        name=name,
                        post_type=post_type,
                        status=Post.DEFAULT_INITIAL_POST_STATUS.value,
                        description=description,
                        size=size,
                        language=language,
                        location=location,
                        people_needed=payload['people_needed'],
                        candidate_description=payload.get('candidate_description'),
                        target_date=target_date,
                        expiration_date=expiration_date
                    )
                    post.update_details(payload, department)

                    if payload.get('highlighted_communities'):
                        post.set_highlighted_communities(tx, payload['highlighted_communities'])

                    if payload.get('required_skills'):
                        Post.validate_required_skills(payload['required_skills'])
                        post.set_required_skills(tx, payload['required_skills'])

                    if payload.get('desired_skills'):
                        Post.validate_desired_skills(payload['desired_skills'])
                        post.set_desired_skills(tx, payload['desired_skills'])

                        # Insert activity details in DB
                        activity_data = {
                            'gig': {
                                'post_id': post.id,
                                'name': post.name
                            },
                            'user': {
                                'user_id': post.owner.id,
                                'name': post.owner.name,
                                'profile_picture_url': post.owner.profile_picture_url
                            }
                        }
                        tx.add(Activity.add_activity(post.owner, ActivityType.GIG_POSTED, data=activity_data))
                        tx.add(
                            ActivityGlobal.add_activity(post.owner.customer, ActivityType.GIG_POSTED, data=activity_data))
                    return post.as_dict()
            raise NotAllowedError(f"User '{owner.id}' has no permission for create a gig")


@blueprint.route('/<post_id>')
class PostByIdAPI(AuthenticatedAPIBase):

    @staticmethod
    def get(post_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['readPermission'] == 'Yes':
                    post = Post.lookup(tx, post_id)
                    if Permissions.check_user_permission(post.owner.customer.id, user.customer_id):
                        return post.as_dict(user=user)
                    raise NotAllowedError("Invalid customer id")
            raise NotAllowedError(f"User '{user.id}' has no permission for to see")

    @staticmethod
    def put(post_id):  # noqa: C901
        with transaction() as tx:
            payload = request.json
            user = User.lookup(tx, current_cognito_jwt['sub'])
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['createPermission'] == 'Yes':
                    post = Post.lookup(tx, post_id)
                    if Permissions.check_user_permission(post.owner.customer.id, user.customer_id):
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
                            'description': {
                                'validate_and_convert': Post.validate_and_convert_description
                            },
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
                            'name': {
                                'validate_and_convert': Post.validate_and_convert_name
                            },
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

                        post.update_details(payload)

                        if 'highlighted_communities' in payload:
                            post.set_highlighted_communities(tx, payload['highlighted_communities'])

                        post.last_updated_at = datetime.utcnow()

                        # Fetch the post again from the database so the updates made above are reflected in the response
                        with transaction() as tx:
                            post = Post.lookup(tx, post_id)
                            return post.as_dict()
                    raise NotAllowedError("Invalid customer id")
            raise NotAllowedError(f"User '{user.id}' has no permission for update")

    @staticmethod
    def delete(post_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['AdminPermission'] == 'Yes':
                    post = Post.lookup(tx, post_id)
                    if Permissions.check_user_permission(post.owner.customer.id, user.customer_id):
                        # For now, only the post owner is allowed to delete the post
                        if post.owner_id != user.id:
                            raise NotAllowedError(f"User '{user.id}' is not the post owner")
                        post.status = PostStatus.DELETED.value
                    return make_no_content_response()
                raise NotAllowedError("Invalid customer id")
            raise NotAllowedError(f"User '{user.id}' has no permission for delete")


@blueprint.route('/<post_id>/video')
class PostVideoAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(post_id):
        # TODO: (sunil) add validation for accepted content types
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['createPermission'] == 'Yes':
                    metadata = {
                        'resource': 'post',
                        'resource_id': post_id,
                        'type': 'video',
                    }
                    return PostVideoAPI.create_user_upload(
                        current_cognito_jwt['sub'], request.json['filename'],
                        request.json['content_type'], 'posts', metadata)
            raise NotAllowedError(f"User '{user.id}' has no permission for update video")


@blueprint.route('/<post_id>/video/<upload_id>')
class PostVideoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(post_id, upload_id):

        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['createPermission'] == 'No':
                    user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
                    post = Post.lookup(tx, post_id)
                    if Permissions.check_user_permission(post.owner.customer.id, user.customer_id):
                        if status == UserUploadStatus.UPLOADED:
                            post.description_video = user_upload
                            user_upload.status = status.value
                        # TODO: (sunil) return an error if this status transition is not supported

                        return {
                            'status': user_upload.status,
                        }
                    raise NotAllowedError("Invalid customer id")
            raise NotAllowedError(f"User '{user.id}' has no permission for update video")

    @staticmethod
    def delete(post_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['AdminPermission'] == 'Yes':
                    user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
                    post = Post.lookup(tx, post_id)
                    if Permissions.check_user_permission(post.owner.customer.id, user.customer_id):
                        # For now, only the post owner is allowed to delete the post video
                        if post.owner_id != user.id:
                            raise NotAllowedError(f"User '{user.id}' is not the post owner")
                        post.description_video = None
                        user_upload.status = UserUploadStatus.DELETED.value
                        return make_no_content_response()
                    raise NotAllowedError("Invalid customer id")
            raise NotAllowedError(f"User '{user.id}' has no permission for delete video")


@blueprint.route('/<post_id>/bookmark')
class PostBookmarkAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(post_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, post_id)
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            # noop if the bookmark already exists, otherwise add one
            # TODO: (sunil) may need to acquire a mutex to handle concurrent requests
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['createPermission'] == 'Yes':
                    if Permissions.check_user_permission(post.owner.customer.id, user.customer_id):
                        bookmark = UserPostBookmark.lookup(tx, user.id, post.id, must_exist=False)
                        if bookmark is None:
                            UserPostBookmark(user=user, post=post, created_at=datetime.utcnow())
                        return make_no_content_response()
                    raise NotAllowedError("Invalid customer id")
            raise NotAllowedError(f"User '{user.id}' has no permission for update bookmark")

    @staticmethod
    def delete(post_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, post_id)
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['createPermission'] == 'Yes':
                    if Permissions.check_user_permission(post.owner.customer.id, user.customer_id):
                        bookmark = UserPostBookmark.lookup(tx, user.id, post.id)
                        tx.delete(bookmark)
                        return make_no_content_response()
                    raise NotAllowedError("Invalid customer id")
            raise NotAllowedError(f"User '{user.id}' has no permission for delete post id")


@blueprint.route('/<post_id>/like')
class PostLikeAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(post_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, post_id)
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            # noop if the like already exists, otherwise add one
            # TODO: (sunil) may need to acquire a mutex to handle concurrent requests
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['createPermission'] == 'Yes':
                    if Permissions.check_user_permission(post.owner.customer.id, user.customer_id):
                        like = UserPostLike.lookup(tx, user.id, post.id, must_exist=False)
                        if like is None:
                            UserPostLike(user=user, post=post, created_at=datetime.utcnow())
                        return make_no_content_response()
                    raise NotAllowedError("Invalid customer id")
            raise NotAllowedError(f"User '{user.id}' has no permission for update like")

    @staticmethod
    def delete(post_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            post = Post.lookup(tx, post_id)
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['AdminPermission'] == 'Yes':
                    if Permissions.check_user_permission(post.owner.customer.id, user.customer_id):
                        like = UserPostLike.lookup(tx, user.id, post.id)
                        tx.delete(like)
                        return make_no_content_response()
                    raise NotAllowedError("Invalid customer id")
            raise NotAllowedError(f"User '{user.id}' has no permission for delete like")


@post_type_blueprint.route('')
class PostTypeAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            query = tx.query(PostType)
            return jsonify([post_type.as_dict() for post_type in query])


@location_blueprint.route('')
class LocationAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            current_user_role = Permissions.get_user_role(tx, current_cognito_jwt['sub'])
            for permission in current_user_role.permissions:
                if permission["api"] == 'Gig' and permission['readPermission'] == 'Yes':
                    query = tx.query(Location).with_parent(user.customer)
                    return jsonify([location.as_dict() for location in query])
            raise NotAllowedError(f"User '{user.id}' has no permission to see like")


@language_blueprint.route('')
class LanguageAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        return jsonify(Language.SUPPORTED_LANGUAGES)
