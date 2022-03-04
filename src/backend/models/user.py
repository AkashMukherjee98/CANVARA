import copy
import enum

from sqlalchemy.orm import backref, relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase
from .language import Language
from .skill import SkillWithLevelMixin, SkillWithoutLevelMixin
from .user_upload import UserUpload


class SkillType(enum.Enum):
    CURRENT_SKILL = 'current_skill'
    DESIRED_SKILL = 'desired_skill'


class UserCurrentSkill(ModelBase, SkillWithLevelMixin):
    __tablename__ = 'user_current_skill'


class UserDesiredSkill(ModelBase, SkillWithoutLevelMixin):
    __tablename__ = 'user_desired_skill'


class User(ModelBase):
    # Note: 'user' is a reserved keyword in PostgreSQL so we use 'canvara_user' instead
    __tablename__ = 'canvara_user'

    profile = None
    customer = relationship("Customer", back_populates="users")
    posts = relationship("Post", back_populates="owner")
    applications = relationship("Application", back_populates="applicant")
    product_preferences = relationship("ProductPreference", secondary='user_product_preference')
    current_skills = relationship("UserCurrentSkill")
    desired_skills = relationship("UserDesiredSkill")
    post_bookmarks = relationship("UserPostBookmark", back_populates="user")
    post_likes = relationship("UserPostLike", back_populates="user")
    profile_picture = relationship(UserUpload, foreign_keys="[User.profile_picture_id]")
    background_picture = relationship(UserUpload, foreign_keys="[User.background_picture_id]")
    team = relationship("User", backref=backref("manager", remote_side='User.id'))
    fun_facts = relationship("UserUpload", secondary='user_fun_fact')
    feedback_list = relationship("Feedback", foreign_keys="Feedback.user_id", back_populates="user")
    mentorship_video = relationship(UserUpload, foreign_keys="[User.mentorship_video_id]")
    community_memberships = relationship("Community", secondary='community_membership', primaryjoin=(
        "and_(CommunityMembership.community_id==Community.id, "
        "CommunityMembership.status == 'active')"))
    bookmark_user = relationship("UserBookmark", foreign_keys="[UserBookmark.bookmarked_user_id]")

    MIN_CURRENT_SKILLS = 3
    MAX_CURRENT_SKILLS = 50
    MAX_DESIRED_SKILLS = 50

    DEFAULT_PROFILE_PICTURE_PATH = 'public/users/blank_profile_picture.png'
    DEFAULT_PROFILE_PICTURE_CONTENT_TYPE = 'image/png'

    DEFAULT_BACKGROUND_PICTURE_PATH = 'public/users/blank_background_picture.png'
    DEFAULT_BACKGROUND_PICTURE_CONTENT_TYPE = 'image/png'

    MAX_VIDEO_FUN_FACTS = 1
    MAX_IMAGE_FUN_FACTS = 10

    @property
    def profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.generate_get_url(signed=False)

        return UserUpload.generate_url(
            'get_object',
            UserUpload.get_bucket_name(),
            User.DEFAULT_PROFILE_PICTURE_PATH,
            User.DEFAULT_PROFILE_PICTURE_CONTENT_TYPE,
            signed=False
        )

    @property
    def background_picture_url(self):
        if self.background_picture:
            return self.background_picture.generate_get_url(signed=False)

        return UserUpload.generate_url(
            'get_object',
            UserUpload.get_bucket_name(),
            User.DEFAULT_BACKGROUND_PICTURE_PATH,
            User.DEFAULT_BACKGROUND_PICTURE_CONTENT_TYPE,
            signed=False
        )

    @classmethod
    def lookup(cls, tx, user_id):
        user = tx.get(cls, user_id)
        if user is None:
            raise DoesNotExistError(f"User '{user_id}' does not exist")
        return user

    def validate_manager(self, manager):
        if manager.id == self.id:
            raise InvalidArgumentError("Manager must not be same as the user")
        return manager

    @classmethod
    def my_bookmarks(
        cls, tx, user
    ):
        peoples = tx.query(cls).join(User.bookmark_user.and_(UserBookmark.user_id == user.id)).\
            order_by(UserBookmark.created_at.desc())

        return peoples

    @classmethod
    def validate_skills(cls, skills, skill_type):
        num_skills_selected = len(skills)
        if skill_type == SkillType.CURRENT_SKILL:
            if num_skills_selected < cls.MIN_CURRENT_SKILLS or num_skills_selected > cls.MAX_CURRENT_SKILLS:
                raise InvalidArgumentError(
                    f"Invalid number of skills: {num_skills_selected}. "
                    f"At least {cls.MIN_CURRENT_SKILLS} and "
                    f"no more than {cls.MAX_CURRENT_SKILLS} skills must be selected.")
        else:
            # No minimum limit for desired skills
            if num_skills_selected > cls.MAX_DESIRED_SKILLS:
                raise InvalidArgumentError(
                    f"Invalid number of skills: {num_skills_selected}. "
                    f"No more than {cls.MAX_DESIRED_SKILLS} skills may be selected.")

        skill_names_seen = set()
        for skill in skills:
            # Make sure there are no duplicate entries
            name = skill['name'].lower()
            if name in skill_names_seen:
                raise InvalidArgumentError(f"Multiple entries found for skill '{skill['name']}'.")
            skill_names_seen.add(name)

            if skill_type == SkillType.DESIRED_SKILL:
                # Ignore level even if it's specified
                continue
            UserCurrentSkill.validate_skill_level(skill['name'], skill.get('level'))

    def set_current_skills(self, tx, skills):
        # TODO: (sunil) Need to lock the user here so no other thread can make updates
        UserCurrentSkill.update_skills(tx, self.customer_id, self.current_skills, skills)

    def set_desired_skills(self, tx, skills):
        # TODO: (sunil) Need to lock the user here so no other thread can make updates
        UserDesiredSkill.update_skills(tx, self.customer_id, self.desired_skills, skills)

    def add_fun_fact(self, fun_fact):
        # User can have at most 1 video and 10 image fun facts
        # If the user already has that many fun facts, remove the oldest ones first
        existing_fun_facts = []
        max_fun_facts = -1
        if fun_fact.is_video():
            existing_fun_facts = [fact for fact in self.fun_facts if fact.is_video()]
            max_fun_facts = self.MAX_VIDEO_FUN_FACTS
        elif fun_fact.is_image():
            existing_fun_facts = [fact for fact in self.fun_facts if fact.is_image()]
            max_fun_facts = self.MAX_IMAGE_FUN_FACTS
        else:
            raise InvalidArgumentError(f"Invalid fun fact type: '{fun_fact.content_type}'")

        if len(existing_fun_facts) >= max_fun_facts:
            sorted_facts = sorted(existing_fun_facts, key=lambda fact: fact.created_at)
            for fact in sorted_facts[:len(sorted_facts) - max_fun_facts + 1]:
                self.fun_facts.remove(fact)
        self.fun_facts.append(fun_fact)

    @property
    def profile_copy(self):
        return copy.deepcopy(self.profile) if self.profile is not None else {}

    def update_profile(self, payload):
        profile = copy.deepcopy(self.profile) if self.profile else {}
        profile_fields = [
            'title',
            'location',
            'linkedin_url',
            'email',
            'phone_number',
            'hidden_secrets',
            'career_goals',
            'superpowers',
            'company_start_date',
            'pronoun',
            'department',
            'introduction',
            'slack_teams_messaging_id',
            'mentorship_description'
        ]
        for field_name in profile_fields:
            if payload.get(field_name) is not None:
                if payload[field_name]:
                    profile[field_name] = payload[field_name]
                elif field_name in profile:
                    # If there was an existing value for this field, and it's now
                    # being set to empty string, remove it instead
                    del profile[field_name]

        if payload.get('languages') is not None:
            if payload['languages']:
                profile['languages'] = Language.validate_and_convert_languages(payload['languages'])
            elif 'languages' in profile:
                del profile['languages']

        profile['hashtags'] = payload['hashtags'] if payload.get('hashtags') is not None else []

        if payload.get('mentorship_offered') is not None:
            if isinstance(payload['mentorship_offered'], bool):
                profile['mentorship_offered'] = payload['mentorship_offered']
            else:
                raise InvalidArgumentError(
                    f"Mentorship Offered accepts true or false, you have provided: {payload['mentorship_offered']}")

        profile['mentorship_hashtags'] = (
            payload['mentorship_hashtags'] if payload.get('mentorship_hashtags') is not None else [])
        self.profile = profile

    def as_summary_dict(self):
        return {
            'user_id': self.id,
            'name': self.name,
            'profile_picture_url': self.profile_picture_url,
        }

    def as_custom_dict(self, labels=None):
        user = {
            'user_id': self.id,
            'name': self.name,
            'profile_picture_url': self.profile_picture_url,
        }

        def add_if_not_none(key, value):
            if (labels is not None and key in labels) and value is not None:
                user[key] = value

        add_if_not_none('title', self.profile.get('title'))
        add_if_not_none('pronoun', self.profile.get('pronoun'))
        add_if_not_none('location', self.profile.get('location'))
        add_if_not_none('department', self.profile.get('department'))
        add_if_not_none('email', self.profile.get('email'))
        add_if_not_none('phone_number', self.profile.get('phone_number'))

        add_if_not_none('slack_teams_messaging_id', self.profile.get('slack_teams_messaging_id'))

        return user

    def as_dict(self, scrub_feedback=False):  # noqa: C901
        user = {
            'customer_id': self.customer_id,
            'user_id': self.id,
            'name': self.name,
        }
        user['product_preferences'] = [pref.as_dict() for pref in self.product_preferences]
        user['current_skills'] = [skill.as_dict() for skill in self.current_skills]
        user['desired_skills'] = [skill.as_dict() for skill in self.desired_skills]
        user['profile_picture_url'] = self.profile_picture_url
        user['background_picture_url'] = self.background_picture_url

        def add_if_not_none(key, value):
            if value is not None:
                user[key] = value

        add_if_not_none('username', self.username)
        add_if_not_none('title', self.profile.get('title'))
        add_if_not_none('location', self.profile.get('location'))
        add_if_not_none('email', self.profile.get('email'))
        add_if_not_none('phone_number', self.profile.get('phone_number'))
        add_if_not_none('linkedin_url', self.profile.get('linkedin_url'))

        add_if_not_none('hidden_secrets', self.profile.get('hidden_secrets'))
        add_if_not_none('career_goals', self.profile.get('career_goals'))
        add_if_not_none('superpowers', self.profile.get('superpowers'))
        add_if_not_none('company_start_date', self.profile.get('company_start_date'))
        add_if_not_none('pronoun', self.profile.get('pronoun'))
        add_if_not_none('department', self.profile.get('department'))
        add_if_not_none('introduction', self.profile.get('introduction'))
        add_if_not_none('languages', self.profile.get('languages'))
        add_if_not_none('allow_demo_mode', self.profile.get('allow_demo_mode'))
        add_if_not_none('onboarding_complete', self.profile.get('onboarding_complete'))
        add_if_not_none('hashtags', self.profile.get('hashtags'))
        add_if_not_none('slack_teams_messaging_id', self.profile.get('slack_teams_messaging_id'))
        add_if_not_none('mentorship_offered', self.profile.get('mentorship_offered'))
        add_if_not_none('mentorship_description', self.profile.get('mentorship_description'))
        add_if_not_none('mentorship_hashtags', self.profile.get('mentorship_hashtags'))

        if self.manager:
            user['manager'] = self.manager.as_summary_dict()

        # if the user has direct reports, 'team' consists of all those direct reports
        # otherwise, if the user has a manager, 'team' is all other users reporting to the same manager, plus the manager
        if self.team:
            user['team'] = [member.as_summary_dict() for member in self.team]
        elif self.manager:
            user['team'] = [self.manager.as_summary_dict()]
            user['team'] += [member.as_summary_dict() for member in self.manager.team if member.id != self.id]

        # Return the fun facts, if present in the following order:
        # - video (at most 1)
        # - images (at most 10)
        # - text
        fun_facts = [fact.as_dict(method='get') for fact in self.fun_facts if fact.is_video()]
        fun_facts.extend([fact.as_dict(method='get') for fact in self.fun_facts if fact.is_image()])
        if self.profile.get('interesting_facts') is not None:
            fun_facts.append(self.profile['interesting_facts'])

        if fun_facts:
            user['fun_facts'] = fun_facts

        # TODO: (sunil) add a max limit to the number of feedback items sent
        if self.feedback_list:
            user['feedback'] = [feedback.as_dict(comments_only=scrub_feedback) for feedback in self.feedback_list]

        if self.mentorship_video:
            user['mentorship_video'] = self.mentorship_video.as_dict(method='get')

        community_memberships = [community.as_summary_dict() for community in self.community_memberships]
        if community_memberships:
            user['community_memberships'] = community_memberships

        return user


class UserBookmark(ModelBase):  # pylint: disable=too-few-public-methods
    __tablename__ = 'user_bookmark'

    user = relationship("User", foreign_keys="[UserBookmark.user_id]")
    bookmarked_user = relationship("User", back_populates="bookmark_user", foreign_keys="[UserBookmark.bookmarked_user_id]")

    @classmethod
    def lookup(cls, tx, user_id, bookmarked_user_id, must_exist=True):
        bookmark = tx.get(cls, (user_id, bookmarked_user_id))
        if bookmark is None and must_exist:
            raise DoesNotExistError(f"Bookmark for user '{bookmarked_user_id}' does not exist")
        return bookmark
