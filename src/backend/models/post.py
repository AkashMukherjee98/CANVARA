from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase
from .language import Language
from .location import Location
from .post_type import PostType
from .user import User


class Post(ModelBase):
    __table__ = db.metadata.tables['post']

    owner = relationship("User", back_populates="posts")
    applications = relationship("Application", back_populates="post")
    post_type = relationship(PostType)
    location = relationship(Location)

    VALID_SIZES = {'S', 'M', 'L'}

    @classmethod
    def lookup(cls, tx, post_id, must_exist=True):
        post = tx.get(cls, post_id)
        if post is None and must_exist:
            raise DoesNotExistError(f"Post '{post_id}' does not exist")
        return post

    @classmethod
    def search(cls, tx, customer_id, owner_id=None, query=None):
        posts = tx.query(cls).join(Post.owner).where(User.customer_id == customer_id)
        if owner_id is not None:
            posts = posts.where(Post.owner_id == owner_id)

        # TODO: (sunil) Use full text search instead
        if query is not None:
            posts = posts.where(or_(
                Post.name.ilike(f'%{query}%'),
                Post.description.ilike(f'%{query}%')
            ))

        return [post.as_dict() for post in posts]

    @classmethod
    def validate_and_convert_target_date(cls, target_date):
        # target_date must be in ISO 8601 format (YYYY-MM-DD)
        try:
            return datetime.fromisoformat(target_date).date()
        except ValueError as ex:
            raise InvalidArgumentError(f"Unable to parse target_date: {target_date}") from ex

    @classmethod
    def validate_and_convert_size(cls, size):
        if size.upper() not in cls.VALID_SIZES:
            raise InvalidArgumentError(f"Invalid size: {size}.")
        return size.upper()

    @classmethod
    def validate_and_convert_language(cls, language):
        if language not in Language.SUPPORTED_LANGUAGES:
            raise InvalidArgumentError(f"Unsupported language: {language}")

    def as_dict(self):
        post = {
            'post_id': self.id,
            'name': self.name,
            'post_type': self.post_type.as_dict(),
            'description': self.description,
            'size': self.size,
            'location': self.location.as_dict(),
            'language': self.language,
            'people_needed': self.people_needed,
            'target_date': self.target_date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'last_updated_at': self.last_updated_at.isoformat(),
        }

        # TODO: (sunil) Remove summary, customer_id and post_owner_id once Frontend has been updated
        post['summary'] = self.name
        post['customer_id'] = self.owner.customer_id
        post['post_owner_id'] = self.owner_id

        post['post_owner'] = {
            'user_id': self.owner_id,
            'name': self.owner.name,
            'profile_picture_url': self.owner.profile_picture_url
        }

        return post
