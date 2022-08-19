from enum import Enum
import copy

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
    feedback = None

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

    @classmethod
    def lookup_by_feedback(cls, tx, author_id, post_id, user_id):
        feedback = tx.query(cls).where(and_(
            cls.author_id == author_id,
            cls.post_id == post_id,
            cls.user_id == user_id
        )).one_or_none()
        if feedback is None:
            raise DoesNotExistError(f"Feedback not given by the author '{author_id}' in the post '{post_id}'")
        return feedback

    def update_feedback(self, payload):
        feedback = copy.deepcopy(self.feedback) if self.feedback else {}
        feedback_fields = [
            'comments',
            'concerns',
            'additional_comments'
        ]

        for field_name in feedback_fields:
            if payload.get(field_name) is not None:
                if payload[field_name]:
                    feedback[field_name] = payload[field_name]
                elif field_name in feedback:
                    del feedback[field_name]

        self.feedback = feedback

    def as_dict(self, comments_only=False):
        feedback = {
            'feedback_id': self.id,
            'post_id': self.post.id,
            'author': self.author.as_custom_dict(['title', 'role', 'pronoun'])
        }

        user_key = 'performer' if self.user_role == FeedbackUserRole.PERFORMER.value else 'post_owner'
        feedback[user_key] = {
            'user_id': self.user.id,
            'name': self.user.name,
        }

        if 'comments' in self.feedback:
            feedback['comments'] = self.feedback['comments']

        if not comments_only:
            if 'concerns' in self.feedback:
                feedback['concerns'] = self.feedback['concerns']

            if 'additional_comments' in self.feedback:
                feedback['additional_comments'] = self.feedback['additional_comments']

        return feedback
