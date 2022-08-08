from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.http import make_no_content_response
from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from backend.models.db import transaction
from backend.models.backgroundpicture import BackgroundPicture
from backend.models.user import User
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('backgroundpicture', __name__, url_prefix='/backgroundpictures')


@blueprint.route('')
class BackgroundPictureAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def get():
        with transaction() as tx:
            backgroundpictures = BackgroundPicture.search(tx)
            backgroundpictures = [backgroundpicture.backgroundpicture.as_dict() for backgroundpicture in backgroundpictures]
        return jsonify(backgroundpictures)

    @staticmethod
    def put():
        user = current_cognito_jwt['sub']
        metadata = {
            'resource': 'user',
            'resource_id': user,
            'type': 'background_picture',
        }
        if 'image' not in request.json['content_type']:
            raise InvalidArgumentError(f"Invalid content type '{request.json['content_type']}'")
        return BackgroundPictureAPI.create_user_upload(
            user, request.json['filename'], request.json['content_type'], 'users', metadata)


@blueprint.route('/<upload_id>')
class BackgroundPictureByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            backgroundpicture = BackgroundPicture.lookup(tx, user.id, user_upload.id)
            if backgroundpicture is None:
                if status == UserUploadStatus.UPLOADED:
                    tx.add(BackgroundPicture(
                            user=user,
                            backgroundpicture=user_upload))
                    user_upload.status = status.value
            else:
                raise DoesNotExistError(f"Background Picture '{backgroundpicture.upload_id}' \
                                    for the user '{backgroundpicture.user_id}' already exist")

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            backgroundpicture = BackgroundPicture.lookup(tx, user.id, user_upload.id)
            if backgroundpicture is not None:
                tx.delete(backgroundpicture)
                user_upload.status = UserUploadStatus.DELETED.value
            else:
                raise DoesNotExistError(f"Background Picture '{backgroundpicture.upload_id}' \
                            for the user '{backgroundpicture.user_id}' does not exist")
        return make_no_content_response()
