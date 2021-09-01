from enum import Enum

from sqlalchemy import and_
from sqlalchemy.orm import contains_eager, joinedload, relationship

from backend.common.exceptions import DoesNotExistError
from .db import ModelBase
from .post import Post
from .user import User


class FeedbackUserRole(Enum):
    PERFORMER = 'performer'
    POSTER = 'poster'


class Feedback(ModelBase):
    __tablename__ = 'feedback'

    author = relationship('User', foreign_keys='Feedback.author_id')
    post = relationship('Post')
    user = relationship('User', foreign_keys='Feedback.user_id', back_populates='feedback_list')

    @classmethod
    def lookup_by_post(cls, tx, post_id):
        # TODO: (sunil) We may need a filter to separate poster feedback from performer feedback
        return tx.query(cls).join(cls.post).where(Post.id == post_id).order_by(cls.created_at.desc())

    @classmethod
    def lookup_by_performer(cls, tx, post_id, performer_id):
        query_options = [
            contains_eager(cls.post),
            contains_eager(cls.user),
            joinedload(cls.author),
        ]

        feedback = tx.query(cls).join(cls.post).join(cls.user).where(and_(
            Post.id == post_id,
            User.id == performer_id,
            cls.user_role == FeedbackUserRole.PERFORMER.value
        )).options(query_options).one_or_none()

        if feedback is None:
            raise DoesNotExistError(f"Feedback for performer '{performer_id}' for post '{post_id}' does not exist")
        return feedback

    def as_dict(self):
        feedback = {
            'feedback_id': self.id,
            'post_id': self.post.id,
            'author': {
                'user_id': self.author.id,
                'name': self.author.name,
            }
        }

        user_key = 'performer' if self.user_role == FeedbackUserRole.PERFORMER.value else 'post_owner'
        feedback[user_key] = {
            'user_id': self.user.id,
            'name': self.user.name,
        }

        if 'comments' in self.feedback:
            feedback['comments'] = self.feedback['comments']

        if 'concerns' in self.feedback:
            feedback['concerns'] = self.feedback['concerns']

        if 'additional_comments' in self.feedback:
            feedback['additional_comments'] = self.feedback['additional_comments']

        return feedback
