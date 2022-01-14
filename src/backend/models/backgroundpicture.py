from sqlalchemy import and_
from sqlalchemy.orm import relationship

from .db import ModelBase
from .user import User
from .user_upload import UserUpload


class BackgroundPicture(ModelBase):
    __tablename__ = 'backgroundpicture'

    user = relationship(User, foreign_keys="[BackgroundPicture.user_id]")
    backgroundpicture = relationship(UserUpload, foreign_keys="[BackgroundPicture.upload_id]")

    @classmethod
    def lookup(cls, tx, user_id, upload_id):

        backgroundpicture = tx.query(cls).where(and_(
            cls.user_id == user_id,
            cls.upload_id == upload_id,
        )).one_or_none()

        return backgroundpicture

    @classmethod
    def search(cls, tx):  # pylint: disable=too-many-arguments
        backgroundpictures = tx.query(cls).all()

        return backgroundpictures
