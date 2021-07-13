from datetime import datetime
from enum import Enum

from sqlalchemy import and_, or_
from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase
from .language import Language
from .location import Location
from .post_type import PostType
from .skill import SkillWithLevelMixin, SkillWithoutLevelMixin
from .user import User
from .user_upload import UserUpload


class PostFilter(Enum):
    # Latest posts available to the current user
    LATEST = 'latest'

    # Active posts owned by the current user
    YOUR = 'your'

    # Posts saved by the current user
    SAVED = 'saved'

    # Posts owned by the current user with work currently underway
    UNDERWAY = 'underway'

    # Posts relevant to the current user
    CURATED = 'curated'

    # Deactivated posts owned by the current user
    DEACTIVATED = 'deactivated'

    @classmethod
    def lookup(cls, name):
        if name is None:
            return None

        try:
            return PostFilter(name.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported filter: {name}.") from ex


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
    user_matches = relationship("UserPostMatch", back_populates="post")
    description_video = relationship(UserUpload)
    bookmark_users = relationship("UserPostBookmark", back_populates="post")
    like_users = relationship("UserPostLike", back_populates="post")

    DEFAULT_INITIAL_POST_STATUS = PostStatus.ACTIVE
    VALID_SIZES = {'S', 'M', 'L'}

    DEFAULT_FILTER = PostFilter.CURATED

    MAX_SKILLS = 5

    @classmethod
    def lookup(cls, tx, post_id, must_exist=True):
        post = tx.get(cls, post_id)
        if post is None and must_exist:
            raise DoesNotExistError(f"Post '{post_id}' does not exist")
        return post

    @classmethod
    def search(
        cls, tx, user, owner_id=None, query=None, post_type_id=None, post_filter=None
    ):  # pylint: disable=too-many-arguments
        if post_filter is None:
            post_filter = cls.DEFAULT_FILTER

        posts = tx.query(cls).join(Post.owner).where(User.customer_id == user.customer_id)
        if owner_id is not None:
            posts = posts.where(Post.owner_id == owner_id)

        if post_type_id is not None:
            posts = posts.where(Post.post_type_id == post_type_id)

        # TODO: (sunil) Use full text search instead
        if query is not None:
            posts = posts.where(or_(
                Post.name.ilike(f'%{query}%'),
                Post.description.ilike(f'%{query}%')
            ))

        # TODO: (sunil) Implement filtering by remaining criteria
        if post_filter == PostFilter.DEACTIVATED:
            posts = posts.where(and_(
                Post.owner_id == user.id,
                Post.status == PostStatus.DEACTIVED.value
            ))
        elif post_filter == PostFilter.LATEST:
            posts = posts.order_by(Post.created_at.desc())
        elif post_filter == PostFilter.YOUR:
            posts = posts.where(Post.owner_id == user.id)
        # elif post_filter == PostFilter.CURATED:
        elif post_filter == PostFilter.SAVED:
            posts = posts.join(Post.bookmark_users)
        # elif post_filter == PostFilter.UNDERWAY:

        return posts

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
            return PostStatus(status.lower()).value
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

    def as_dict(self, user_id=None):
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

        optional_fields = ['candidate_description']
        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                post[field] = value

        if self.description_video:
            post['video_url'] = self.description_video.generate_presigned_get_url()

        # TODO: (sunil) See if this can be done at lookup time
        if user_id is not None:
            for match in self.user_matches:
                if match.user_id == user_id:
                    post['match_level'] = match.confidence_level
                    break

            post['is_bookmarked'] = any(bookmark.user_id == user_id for bookmark in self.bookmark_users)
            post['is_liked'] = any(like.user_id == user_id for like in self.like_users)

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


class UserPostBookmark(ModelBase):  # pylint: disable=too-few-public-methods
    __table__ = db.metadata.tables['user_post_bookmark']

    user = relationship("User", back_populates="post_bookmarks")
    post = relationship("Post", back_populates="bookmark_users")

    @classmethod
    def lookup(cls, tx, user_id, post_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, post_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Bookmark for post '{post_id}' for user '{user_id}' does not exist")
        return bookmark


class UserPostLike(ModelBase):  # pylint: disable=too-few-public-methods
    __table__ = db.metadata.tables['user_post_like']

    user = relationship("User", back_populates="post_likes")
    post = relationship("Post", back_populates="like_users")

    @classmethod
    def lookup(cls, tx, user_id, post_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, post_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Like for post '{post_id}' for user '{user_id}' does not exist")
        return bookmark
