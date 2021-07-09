import enum
import os.path
import uuid

import boto3

from backend.common.config import get_canvara_config
from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase


class UserUploadStatus(enum.Enum):
    # Upload request has been created but file may not have been uploaded yet
    CREATED = 'created'

    # File has been successfully uploaded
    UPLOADED = 'uploaded'

    @classmethod
    def lookup(cls, status):
        try:
            return UserUploadStatus(status.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported status: {status}.") from ex


class UserUpload(ModelBase):
    __table__ = db.metadata.tables['user_upload']

    __bucket_name = None

    @classmethod
    def lookup(cls, tx, upload_id, customer_id):
        user_upload = tx.get(UserUpload, upload_id)
        if user_upload is None or user_upload.customer_id != customer_id:
            raise DoesNotExistError(f"Upload '{upload_id}' does not exist")
        return user_upload

    @classmethod
    def get_bucket_name(cls):
        if cls.__bucket_name is None:
            canvara_config = get_canvara_config()
            cls.__bucket_name = canvara_config['user_uploads']['s3_bucket']
        return cls.__bucket_name

    @staticmethod
    def generate_upload_path(customer_id, resource, filename):
        _, extension = os.path.splitext(filename)
        filename = f'{str(uuid.uuid4())}{extension}'

        # All user uploads are partitioned by customer id
        # Within the customer directory, files are separated based on the resource - posts, applications, user etc.
        return f'{customer_id}/{resource}/{filename}'

    def generate_presigned_get(self):
        return UserUpload.__generate_presigned_url(self.bucket, self.path, 'get_object')

    @classmethod
    def generate_presigned_put(cls, bucket, path):
        return cls.__generate_presigned_url(bucket, path, 'put_object')

    @classmethod
    def __generate_presigned_url(cls, bucket, path, method):
        return boto3.client('s3').generate_presigned_url(
            ClientMethod=method,
            Params={'Bucket': bucket, 'Key': path}
        )
