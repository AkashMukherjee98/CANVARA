from datetime import datetime
from enum import Enum
import itertools

from sqlalchemy import and_, nullslast, or_
from sqlalchemy.orm import contains_eager, joinedload, noload, relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .location import Location
from .match import UserPostMatch
from .post_type import PostType
from .skill import SkillWithLevelMixin
from .user import User
from .user_upload import UserUpload


class PostFilter(Enum):
    # Most relevant active posts for the user
    RECOMMENDED = 'recommended'

    # Latest active posts recommended for the user
    LATEST = 'latest'

    # Active and deactivated posts owned by the user,
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

    # Post has been deleted and can no longer be accessed by any user
    DELETED = 'deleted'


class PostSkillType(Enum):
    REQUIRED_SKILL = 'required_skills'
    DESIRED_SKILL = 'desired_skills'


class PostSkill(ModelBase, SkillWithLevelMixin):
    __tablename__ = 'post_skill'

    @classmethod
    def create_desired_skill(cls, level, skill):
        return cls(level=level, skill=skill, is_required=False)

    @classmethod
    def create_required_skill(cls, level, skill):
        return cls(level=level, skill=skill, is_required=True)


class Post(ModelBase):
    __tablename__ = 'post'

    owner = relationship("User", back_populates="posts")
    applications = relationship("Application", back_populates="post")
    post_type = relationship(PostType)
    location = relationship(Location)

    required_skills = relationship("PostSkill", primaryjoin='and_(Post.id == PostSkill.post_id, PostSkill.is_required)')
    desired_skills = relationship("PostSkill", primaryjoin='and_(Post.id == PostSkill.post_id, not_(PostSkill.is_required))')
    user_matches = relationship("UserPostMatch", back_populates="post")
    description_video = relationship(UserUpload)
    bookmark_users = relationship("UserPostBookmark", back_populates="post")
    like_users = relationship("UserPostLike", back_populates="post")

    DEFAULT_INITIAL_POST_STATUS = PostStatus.ACTIVE
    VALID_SIZES = {'S', 'M', 'L'}

    DEFAULT_FILTER = PostFilter.RECOMMENDED

    MAX_SKILLS = 20

    MAX_NAME_LENGTH = 48

    @classmethod
    def lookup(cls, tx, post_id, must_exist=True):
        post = tx.query(cls).where(and_(
            cls.id == post_id,
            cls.status != PostStatus.DELETED.value,
        )).one_or_none()
        if post is None and must_exist:
            raise DoesNotExistError(f"Post '{post_id}' does not exist")
        return post

    @classmethod
    def __apply_search_filter(cls, posts, user, post_filter):
        # Exclude posts if user is already applied for
        # It won't apply if custom filter BOOKMARKED/MY_APPLICATIONS/MY_WORK is applied
        if post_filter not in [PostFilter.BOOKMARKED, PostFilter.MY_APPLICATIONS, PostFilter.MY_WORK]:
            from .application import Application, ApplicationStatus  # pylint: disable=import-outside-toplevel, cyclic-import
            posts = posts.outerjoin(Post.applications.and_(
                Application.user_id == user.id,
                Application.status != ApplicationStatus.DELETED.value
            )).where(Application.user_id.is_(None))

        if post_filter == PostFilter.DEACTIVATED:
            posts = posts.where(and_(
                Post.owner_id == user.id,
                Post.status == PostStatus.DEACTIVED.value
            ))

        elif post_filter == PostFilter.LATEST:
            posts = posts.where(and_(
                Post.owner_id != user.id,
                Post.status == PostStatus.ACTIVE.value,
            )).order_by(Post.created_at.desc())

        elif post_filter == PostFilter.MY_POSTS:
            # My posts includes both active and deactivated posts
            # This is to allow the user to re-activate one of their posts
            # TODO: (sunil) add support for drafts
            posts = posts.where(Post.owner_id == user.id).\
                order_by(Post.created_at.desc())

        elif post_filter == PostFilter.RECOMMENDED:
            posts = posts.where(and_(
                Post.owner_id != user.id,
                Post.status == PostStatus.ACTIVE.value,
            )).order_by(nullslast(UserPostMatch.confidence_level.desc()))

        elif post_filter == PostFilter.BOOKMARKED:
            posts = posts.join(Post.bookmark_users.and_(UserPostBookmark.user_id == user.id)).\
                order_by(UserPostBookmark.created_at.desc())

        elif post_filter == PostFilter.MY_APPLICATIONS:
            # TODO: (sunil) add support for drafts
            from .application import Application, ApplicationStatus  # pylint: disable=import-outside-toplevel, cyclic-import

            # Return posts that have a new, shortlisted or rejected application
            # Selected applications will show up only in "my work"
            posts = posts.join(Post.applications.and_(
                Application.user_id == user.id,
                Application.status.in_([
                    ApplicationStatus.NEW.value,
                    ApplicationStatus.SHORTLISTED.value,
                    ApplicationStatus.PASSED.value])
            )).order_by(Application.created_at.desc())

        elif post_filter == PostFilter.MY_WORK:
            from .application import Application, ApplicationStatus  # pylint: disable=import-outside-toplevel, cyclic-import
            posts = posts.join(Post.applications.and_(
                Application.user_id == user.id,
                Application.status == ApplicationStatus.SELECTED.value
            )).order_by(Application.created_at.desc())
        return posts

    @classmethod
    def search(
        cls, tx, user, owner_id=None, query=None, post_type_id=None, post_filter=None, limit=None
    ):  # pylint: disable=too-many-arguments
        if post_filter is None:
            post_filter = cls.DEFAULT_FILTER

        # Get all non-deleted posts within this customer account
        posts = tx.query(cls).join(Post.owner).where(and_(
            User.customer_id == user.customer_id,
            cls.status != PostStatus.DELETED.value,
        ))

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

        # Eagerload UserPostMatch since we will need it later on
        # Filter the join by user id to force the relationship to be one-to-zero-or-one,
        # so that eagerloading doesn't bring in any additional rows
        if limit is not None:
            posts = posts.outerjoin(Post.user_matches.and_(UserPostMatch.user_id == user.id)).limit(limit)
        else:
            posts = posts.outerjoin(Post.user_matches.and_(UserPostMatch.user_id == user.id))

        # Eagerload other columns
        # Avoid loading the more expensive attributes like skills, which are one-to-many,
        # and video, which require expensive presigned url generation.
        # These attributes are not strictly needed in the search results
        # TODO: (sunil) Change the list posts API specification to make it formal that
        #               these expensive attributes will not be returned.
        query_options = [
            contains_eager(Post.owner).joinedload(User.profile_picture),
            joinedload(Post.post_type, innerjoin=True),
            joinedload(Post.location, innerjoin=True),
            noload(Post.required_skills),
            noload(Post.desired_skills),
            noload(Post.description_video),
            contains_eager(Post.user_matches),
            noload(Post.like_users)
        ]

        # Don't load UserPostBookmark unless we have already joined with it because of the 'bookmarked' filter
        if post_filter == PostFilter.BOOKMARKED:
            query_options.append(contains_eager(Post.bookmark_users))
        else:
            query_options.append(noload(Post.bookmark_users))

        posts = posts.options(query_options)
        return posts

    @classmethod
    def validate_and_convert_name(cls, name):
        if len(name) > cls.MAX_NAME_LENGTH:
            raise InvalidArgumentError(f"Name must not be more than {cls.MAX_NAME_LENGTH} characters.")
        return name

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

            PostSkill.validate_skill_level(skill['name'], skill.get('level'))
        return skills

    @classmethod
    def validate_required_skills(cls, skills):
        return cls.__validate_skills(skills, PostSkillType.REQUIRED_SKILL)

    @classmethod
    def validate_desired_skills(cls, skills):
        return cls.__validate_skills(skills, PostSkillType.DESIRED_SKILL)

    def set_required_skills(self, tx, skills):
        # TODO: (sunil) Need to lock the user here so no other thread can make updates
        PostSkill.update_skills(
            tx, self.owner.customer_id, self.required_skills, skills, factory=PostSkill.create_required_skill)

    def set_desired_skills(self, tx, skills):
        # TODO: (sunil) Need to lock the user here so no other thread can make updates
        PostSkill.update_skills(
            tx, self.owner.customer_id, self.desired_skills, skills, factory=PostSkill.create_desired_skill)

    def match_user_skills(self, user):
        matched_skills = []
        unmatched_skills = []
        for post_skill in itertools.chain(self.required_skills, self.desired_skills):
            if any(post_skill.matches(user_skill) for user_skill in user.current_skills):
                matched_skills.append(post_skill)
            else:
                unmatched_skills.append(post_skill)
        return matched_skills, unmatched_skills

    def as_dict(self, user=None):
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

        if self.candidate_description:
            post['candidate_description'] = self.candidate_description

        if self.description_video:
            # TODO: (sunil) remove this once Frontend has been updated
            post['video_url'] = self.description_video.generate_get_url()
            post['description_video'] = self.description_video.as_dict(method='get')

        # TODO: (sunil) See if this can be done at lookup time
        if user is not None:
            for match in self.user_matches:
                if match.user_id == user.id:
                    post['match_level'] = match.confidence_level
                    break

            if self.required_skills or self.desired_skills:
                matched_skills, unmatched_skills = self.match_user_skills(user)
                post['matched_skills'] = [skill.as_dict() for skill in matched_skills]
                post['unmatched_skills'] = [skill.as_dict() for skill in unmatched_skills]

            post['is_bookmarked'] = any(bookmark.user_id == user.id for bookmark in self.bookmark_users)
            post['is_liked'] = any(like.user_id == user.id for like in self.like_users)

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
    __tablename__ = 'user_post_bookmark'

    user = relationship("User", back_populates="post_bookmarks")
    post = relationship("Post", back_populates="bookmark_users")

    @classmethod
    def lookup(cls, tx, user_id, post_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, post_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Bookmark for post '{post_id}' for user '{user_id}' does not exist")
        return bookmark


class UserPostLike(ModelBase):  # pylint: disable=too-few-public-methods
    __tablename__ = 'user_post_like'

    user = relationship("User", back_populates="post_likes")
    post = relationship("Post", back_populates="like_users")

    @classmethod
    def lookup(cls, tx, user_id, post_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, post_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Like for post '{post_id}' for user '{user_id}' does not exist")
        return bookmark
