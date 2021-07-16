from datetime import datetime
from enum import Enum

from sqlalchemy import and_, nullslast, or_
from sqlalchemy.orm import contains_eager, joinedload, relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase
from .language import Language
from .location import Location
from .match import UserPostMatch
from .post_type import PostType
from .skill import SkillWithLevelMixin, SkillWithoutLevelMixin
from .user import User
from .user_upload import UserUpload


class PostFilter(Enum):
    # Most relevant posts for the user
    RECOMMENDED = 'recommended'

    # Latest posts recommended for the user
    LATEST = 'latest'

    # Active posts owned by the user,
    # sorted by status and creation time with drafts on top
    MY_POSTS = 'myposts'

    # Posts to which the user has applied,
    # sorted by status and creation time with drafts on top
    MY_APPLICATIONS = 'myapplications'

    # Posts on which the user has been selected to work,
    # sorted by status and time they were chosen or work started
    MY_WORK = 'mywork'

    # Posts saved by the user
    BOOKMARKED = 'bookmarked'

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

    DEFAULT_FILTER = PostFilter.RECOMMENDED

    MAX_SKILLS = 5

    @classmethod
    def lookup(cls, tx, post_id, must_exist=True):
        post = tx.get(cls, post_id)
        if post is None and must_exist:
            raise DoesNotExistError(f"Post '{post_id}' does not exist")
        return post

    @classmethod
    def __apply_search_filter(cls, posts, user, post_filter):
        if post_filter == PostFilter.DEACTIVATED:
            posts = posts.where(and_(
                Post.owner_id == user.id,
                Post.status == PostStatus.DEACTIVED.value
            ))

        elif post_filter == PostFilter.LATEST:
            posts = posts.where(Post.owner_id != user.id).\
                order_by(Post.created_at.desc())

        elif post_filter == PostFilter.MY_POSTS:
            # TODO: (sunil) add check for status
            # TODO: (sunil) add support for drafts
            posts = posts.where(Post.owner_id == user.id).\
                order_by(Post.created_at.desc())

        elif post_filter == PostFilter.RECOMMENDED:
            posts = posts.where(Post.owner_id != user.id).\
                order_by(nullslast(UserPostMatch.confidence_level.desc()))

        elif post_filter == PostFilter.BOOKMARKED:
            posts = posts.join(Post.bookmark_users.and_(UserPostBookmark.user_id == user.id)).\
                order_by(UserPostBookmark.created_at.desc())

        elif post_filter == PostFilter.MY_APPLICATIONS:
            # TODO: (sunil) add support for drafts
            from .application import Application  # pylint: disable=import-outside-toplevel, cyclic-import
            posts = posts.join(Post.applications.and_(Application.user_id == user.id)).\
                order_by(Application.created_at.desc())

        elif post_filter == PostFilter.MY_WORK:
            # TODO: (sunil) implement this
            raise NotImplementedError()
        return posts

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

        try:
            posts = cls.__apply_search_filter(posts, user, post_filter)
        except NotImplementedError:
            return []

        # Eagerload UserPostMatch, UserPostBookmark etc. since we will need them later on
        # Filter the joins by user id to force these relationships to be one-to-zero-or-one,
        # so that eagerloading doesn't bring in any additional rows
        posts = posts.\
            outerjoin(Post.user_matches.and_(UserPostMatch.user_id == user.id)).\
            outerjoin(Post.like_users.and_(UserPostLike.user_id == user.id))

        # If we have already joined with UserPostBookmark because of the 'bookmarked' filter, don't join again
        if post_filter != PostFilter.BOOKMARKED:
            posts = posts.outerjoin(Post.bookmark_users.and_(UserPostBookmark.user_id == user.id))

        # Eagerload other columns needed later one
        # TODO: (sunil) Consider changing list_posts operation to just return a summary for each post
        #               instead of full post detail. Then we won't need to load the more expensive
        #               attributes like skills.
        posts = posts.options(
            contains_eager(Post.owner).joinedload(User.profile_picture),
            joinedload(Post.post_type, innerjoin=True),
            joinedload(Post.location, innerjoin=True),
            joinedload(Post.required_skills).joinedload(PostRequiredSkill.skill, innerjoin=True),
            joinedload(Post.desired_skills).joinedload(PostDesiredSkill.skill, innerjoin=True),
            joinedload(Post.description_video),
            contains_eager(Post.user_matches),
            contains_eager(Post.bookmark_users),
            contains_eager(Post.like_users))
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
