from backend.models.db import transaction
from backend.models.user_upload import UserUpload
from backend.models.user import User


class UserUploadMixin:  # pylint: disable=too-few-public-methods
    @staticmethod
    def create_user_upload(user_id, filename, content_type, directory, metadata):
        metadata.update(user_id=user_id, original_filename=filename)
        with transaction() as tx:
            user = User.lookup(tx, user_id)
            user_upload = UserUpload.create_user_upload(user.customer_id, directory, filename, content_type, metadata)
            tx.add(user_upload)
            return user_upload.as_dict()
