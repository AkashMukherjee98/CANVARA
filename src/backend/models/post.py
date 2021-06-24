from sqlalchemy import or_
from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError
from .db import db, ModelBase
from .user import User


class Post(ModelBase):
    __table__ = db.metadata.tables['post']

    owner = relationship("User", back_populates="posts")
    applications = relationship("Application", back_populates="post")

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
                Post.details['summary'].as_string().like(f'%{query}%'),
                Post.details['description'].as_string().like(f'%{query}%')
            ))

        return [post.as_dict() for post in posts]

    def as_dict(self):
        post = {
            'customer_id': self.owner.customer_id,
            'post_id': self.id,
            'post_owner_id': self.owner_id,
            'created_at': self.created_at.isoformat(),
            'last_updated_at': self.last_updated_at.isoformat(),
        }

        def add_if_not_none(key, value):
            if value is not None:
                post[key] = value

        add_if_not_none('summary', self.details.get('summary'))
        add_if_not_none('description', self.details.get('description'))

        add_if_not_none('size', self.details.get('size'))
        add_if_not_none('target_date', self.details.get('target_date'))

        return post
