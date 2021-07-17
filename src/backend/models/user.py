import copy
import enum

from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase
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

    customer = relationship("Customer", back_populates="users")
    posts = relationship("Post", back_populates="owner")
    applications = relationship("Application", back_populates="applicant")
    product_preferences = relationship("ProductPreference", secondary=db.metadata.tables['user_product_preference'])
    current_skills = relationship("UserCurrentSkill")
    desired_skills = relationship("UserDesiredSkill")
    post_bookmarks = relationship("UserPostBookmark", back_populates="user")
    post_likes = relationship("UserPostLike", back_populates="user")
    profile_picture = relationship(UserUpload)

    MIN_CURRENT_SKILLS = 3
    MAX_CURRENT_SKILLS = 10
    MAX_DESIRED_SKILLS = 10

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

        add_if_not_none('title', self.profile.get('title'))
        add_if_not_none('linkedin_url', self.profile.get('linkedin_url'))

        return user
