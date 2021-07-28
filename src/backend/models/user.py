import copy
import enum

from sqlalchemy.orm import backref, relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase
from .language import Language
from .location import Location
from .skill import SkillWithLevelMixin, SkillWithoutLevelMixin
from .user_upload import UserUpload


class SkillType(enum.Enum):
    CURRENT_SKILL = 'current_skill'
    DESIRED_SKILL = 'desired_skill'


class UserCurrentSkill(ModelBase, SkillWithLevelMixin):
    __table__ = db.metadata.tables['user_current_skill']


class UserDesiredSkill(ModelBase, SkillWithoutLevelMixin):
    __table__ = db.metadata.tables['user_desired_skill']


class User(ModelBase):
    # Note: 'user' is a reserved keyword in PostgreSQL so we use 'canvara_user' instead
    __table__ = db.metadata.tables['canvara_user']

    profile = None
    customer = relationship("Customer", back_populates="users")
    posts = relationship("Post", back_populates="owner")
    applications = relationship("Application", back_populates="applicant")
    product_preferences = relationship("ProductPreference", secondary=db.metadata.tables['user_product_preference'])
    current_skills = relationship("UserCurrentSkill")
    desired_skills = relationship("UserDesiredSkill")
    post_bookmarks = relationship("UserPostBookmark", back_populates="user")
    post_likes = relationship("UserPostLike", back_populates="user")
    profile_picture = relationship(UserUpload)
    team = relationship("User", backref=backref("manager", remote_side='User.id'))
    location = relationship(Location)
    fun_facts = relationship("UserUpload", secondary=db.metadata.tables['user_fun_fact'])

    MIN_CURRENT_SKILLS = 3
    MAX_CURRENT_SKILLS = 50
    MAX_DESIRED_SKILLS = 50

    DEFAULT_PROFILE_PICTURE_PATH = 'public/users/blank_profile_picture.png'
    DEFAULT_PROFILE_PICTURE_CONTENT_TYPE = 'image/png'

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

    @property
    def profile_copy(self):
        return copy.deepcopy(self.profile) if self.profile is not None else {}

    def update_profile(self, payload):
        profile = copy.deepcopy(self.profile) if self.profile else {}
        profile_fields = [
            'title',
            'linkedin_url',
            'email',
            'phone_number',
            'hidden_secrets',
            'career_goals',
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
        self.profile = profile

    def as_summary_dict(self):
        return {
            'user_id': self.id,
            'name': self.name,
            'profile_picture_url': self.profile_picture_url,
        }

    def as_dict(self):
        user = {
            'customer_id': self.customer_id,
            'user_id': self.id,
            'name': self.name,
        }
        user['product_preferences'] = [pref.as_dict() for pref in self.product_preferences]
        user['current_skills'] = [skill.as_dict() for skill in self.current_skills]
        user['desired_skills'] = [skill.as_dict() for skill in self.desired_skills]
        user['profile_picture_url'] = self.profile_picture_url

        def add_if_not_none(key, value):
            if value is not None:
                user[key] = value

        add_if_not_none('username', self.username)
        add_if_not_none('title', self.profile.get('title'))
        add_if_not_none('email', self.profile.get('email'))
        add_if_not_none('phone_number', self.profile.get('phone_number'))
        add_if_not_none('linkedin_url', self.profile.get('linkedin_url'))

        add_if_not_none('hidden_secrets', self.profile.get('hidden_secrets'))
        add_if_not_none('career_goals', self.profile.get('career_goals'))
        add_if_not_none('languages', self.profile.get('languages'))

        if self.location:
            user['location'] = self.location.as_dict()

        if self.manager:
            user['manager'] = self.manager.as_summary_dict()

        # if the user has direct reports, 'team' consists of all those direct reports
        # otherwise, if the user has a manager, 'team' is all other users reporting to the same manager
        if self.team:
            user['team'] = [member.as_summary_dict() for member in self.team]
        elif self.manager:
            user['team'] = [member.as_summary_dict() for member in self.manager.team if member.id != self.id]

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

        return user
