from datetime import datetime
from enum import Enum

from sqlalchemy import or_
from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase
from .language import Language
from .location import Location
from .post_type import PostType
from .skill import SkillWithLevelMixin, SkillWithoutLevelMixin
from .user import User


class PostStatus(Enum):
    # Post is available for new applications
    ACTIVE = 'active'

    # Post has been deactivated and is not visible to anyone other than post owner
    DEACTIVED = 'deactivated'

    # Post has expired and is not available for new applications
    EXPIRED = 'expired'

    # TODO: (sunil) Add more statuses


class PostSkillType(Enum):
    REQUIRED_SKILL = 'required_skills'
    DESIRED_SKILL = 'desired_skills'


class PostRequiredSkill(ModelBase, SkillWithLevelMixin):
    __table__ = db.metadata.tables['post_required_skill']


class PostDesiredSkill(ModelBase, SkillWithoutLevelMixin):
    __table__ = db.metadata.tables['post_desired_skill']


class Post(ModelBase):
    __table__ = db.metadata.tables['post']

    owner = relationship("User", back_populates="posts")
    applications = relationship("Application", back_populates="post")
    post_type = relationship(PostType)
    location = relationship(Location)
    required_skills = relationship("PostRequiredSkill")
    desired_skills = relationship("PostDesiredSkill")

    DEFAULT_INITIAL_POST_STATUS = PostStatus.ACTIVE
    VALID_SIZES = {'S', 'M', 'L'}

    # TODO: (sunil) Separate production from other stacks
    DEFAULT_VIDEO_URL = 'https://canvara.s3.us-west-2.amazonaws.com/prototype/user_uploads/post-video-stock.mp4'

    MAX_SKILLS = 5

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
    def __validate_and_convert_isoformat_date(cls, date, fieldname):
        # date must be in ISO 8601 format (YYYY-MM-DD)
        try:
            return datetime.fromisoformat(date).date()
        except ValueError as ex:
            raise InvalidArgumentError(f"Unable to parse {fieldname}: {date}") from ex

    @classmethod
    def validate_and_convert_target_date(cls, target_date):
        return cls.__validate_and_convert_isoformat_date(target_date, 'target_date')

    @classmethod
    def validate_and_convert_expiration_date(cls, expiration_date):
        return cls.__validate_and_convert_isoformat_date(expiration_date, 'expiration_date')

    @classmethod
    def validate_and_convert_size(cls, size):
        if size.upper() not in cls.VALID_SIZES:
            raise InvalidArgumentError(f"Invalid size: {size}.")
        return size.upper()

    @classmethod
    def validate_and_convert_language(cls, language):
        if language not in Language.SUPPORTED_LANGUAGES:
            raise InvalidArgumentError(f"Unsupported language: {language}")
        return language

    @staticmethod
    def validate_and_convert_status(status):
        try:
            # TODO: (sunil) Make sure the transition from current status to this new status is allowed
            return PostStatus(status.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Invalid status: {status}.") from ex

    @classmethod
    def __validate_skills(cls, skills, skill_type):
        if len(skills) > cls.MAX_SKILLS:
            raise InvalidArgumentError(
                f"Invalid number of {skill_type.value}: {len(skills)}. "
                f"No more than {cls.MAX_SKILLS} skills may be selected.")

        skill_names_seen = set()
        for skill in skills:
            # Make sure there are no duplicate entries
            name = skill['name'].lower()
            if name in skill_names_seen:
                raise InvalidArgumentError(f"Multiple entries found for {skill_type.value} '{skill['name']}'.")
            skill_names_seen.add(name)

            if skill_type == PostSkillType.DESIRED_SKILL:
                # Ignore level even if it's specified
                continue
            PostRequiredSkill.validate_skill_level(skill['name'], skill.get('level'))
        return skills

    @classmethod
    def validate_required_skills(cls, skills):
        return cls.__validate_skills(skills, PostSkillType.REQUIRED_SKILL)

    @classmethod
    def validate_desired_skills(cls, skills):
        return cls.__validate_skills(skills, PostSkillType.DESIRED_SKILL)

    def set_required_skills(self, tx, skills):
        # TODO: (sunil) Need to lock the user here so no other thread can make updates
        PostRequiredSkill.update_skills(tx, self.owner.customer_id, self.required_skills, skills)

    def set_desired_skills(self, tx, skills):
        # TODO: (sunil) Need to lock the user here so no other thread can make updates
        PostDesiredSkill.update_skills(tx, self.owner.customer_id, self.desired_skills, skills)

    def as_dict(self):
        post = {
            'post_id': self.id,
            'name': self.name,
            'post_type': self.post_type.as_dict(),
            'status': self.status,
            'description': self.description,
            'size': self.size,
            'location': self.location.as_dict(),
            'language': self.language,
            'people_needed': self.people_needed,
            'target_date': self.target_date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'last_updated_at': self.last_updated_at.isoformat(),
        }

        if self.required_skills:
            post['required_skills'] = [skill.as_dict() for skill in self.required_skills]

        if self.desired_skills:
            post['desired_skills'] = [skill.as_dict() for skill in self.desired_skills]

        if self.expiration_date:
            post['expiration_date'] = self.expiration_date.isoformat()

        optional_fields = ['candidate_description', 'video_url']
        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                post[field] = value

        # TODO: (sunil) Implement match calculation
        post['match_level'] = 75

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
