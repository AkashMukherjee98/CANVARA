from datetime import datetime
import enum
import os.path
import uuid

from sqlalchemy import and_
import boto3

from backend.common.config import get_canvara_config
from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase


S3_BUCKET_PUBLIC_URL_FORMAT = 'https://{bucket}.s3.amazonaws.com/{path}'


class UserUploadStatus(enum.Enum):
    # Upload request has been created but file may not have been uploaded yet
    CREATED = 'created'

    # File has been successfully uploaded
    UPLOADED = 'uploaded'

    # File has been marked for deletion
    DELETED = 'deleted'

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
        user_upload = tx.query(UserUpload).where(and_(
            UserUpload.id == upload_id,
            UserUpload.status != UserUploadStatus.DELETED.value,
            UserUpload.customer_id == customer_id
        )).one_or_none()
        if user_upload is None:
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

    def generate_get_url(self, signed=True):
        return UserUpload.generate_url(
            'get_object',
            self.bucket,
            self.path,
            self.content_type,
            signed=signed
        )

    def generate_put_url(self):
        return self.generate_url(
            'put_object',
            self.bucket,
            self.path,
            self.content_type,
            signed=True
        )

    @classmethod
    def generate_url(cls, method, bucket, path, content_type, signed=True):  # pylint: disable=too-many-arguments
        if not signed:
            assert method == 'get_object', 'Unsigned urls must be GET'

            # TODO: (sunil) Using botocore.UNSIGNED still appears to be too slow.
            #               See if there is a better way than hardcoding the S3 URL
            return S3_BUCKET_PUBLIC_URL_FORMAT.format(bucket=bucket, path=path)

        params = {'Bucket': bucket, 'Key': path}
        if content_type is not None:
            param_name = 'ResponseContentType' if method == 'get_object' else 'ContentType'
            params[param_name] = content_type

        return boto3.client('s3').generate_presigned_url(
            ClientMethod=method,
            Params=params
        )

    @classmethod
    def create_user_upload(
        cls, customer_id, subdirectory, original_filename, content_type, metadata
    ):  # pylint: disable=too-many-arguments
        path = UserUpload.generate_upload_path(customer_id, subdirectory, original_filename)
        return UserUpload(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            bucket=UserUpload.get_bucket_name(),
            path=path,
            content_type=content_type,
            status=UserUploadStatus.CREATED.value,
            metadata=metadata,
            created_at=datetime.utcnow()
        )

    def is_video(self):
        return self.content_type.startswith('video/')

    def is_image(self):
        return self.content_type.startswith('image/')

    def as_dict(self, method='put', signed=True):
        if method == 'put':
            return {
                'upload_id': self.id,
                'url': self.generate_put_url()
            }

        return {
            'upload_id': self.id,
            'content_type': self.content_type,
            'url': self.generate_get_url(signed=signed)
        }
