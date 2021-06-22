import copy
import enum

from sqlalchemy.orm import relationship

from common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase
from .skill import Skill

class SkillType(enum.Enum):
    CURRENT_SKILL = 'current_skill'
    DESIRED_SKILL = 'desired_skill'

class UserCurrentSkill(ModelBase):
    __table__ = db.metadata.tables['user_current_skill']
    skill = relationship("Skill")

    @property
    def id(self):
        return self.skill.id

    def as_dict(self):
        d = self.skill.as_dict()
        d['level'] = self.level
        return d

class UserDesiredSkill(ModelBase):
    __table__ = db.metadata.tables['user_desired_skill']
    skill = relationship("Skill")

    @property
    def id(self):
        return self.skill.id

    def as_dict(self):
        return self.skill.as_dict()

class User(ModelBase):
    # Note: 'user' is a reserved keyword in PostgreSQL so we use 'canvara_user' instead
    __table__ = db.metadata.tables['canvara_user']

    customer = relationship("Customer", back_populates="users")
    posts = relationship("Post", back_populates="owner")
    applications = relationship("Application", back_populates="applicant")
    product_preferences = relationship("ProductPreference", secondary=db.metadata.tables['user_product_preference'])
    current_skills = relationship("UserCurrentSkill")
    desired_skills = relationship("UserDesiredSkill")

    MIN_CURRENT_SKILLS = 3
    MAX_CURRENT_SKILLS = 10
    MAX_DESIRED_SKILLS = 10
    MIN_SKILL_LEVEL = 1
    MAX_SKILL_LEVEL = 10

    @classmethod
    def lookup(cls, tx, id):
        user = tx.get(cls, id)
        if user is None:
            raise DoesNotExistError(f"User '{id}' does not exist")
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
            name = skill['name']
            if name in skill_names_seen:
                raise InvalidArgumentError(f"Multiple entries found for skill '{name}'.")
            skill_names_seen.add(name)

            if skill_type == SkillType.DESIRED_SKILL:
                # Ignore level even if it's specified
                continue

            level = skill.get('level')
            if level is None:
                raise InvalidArgumentError(f"Level is required for skill '{name}'.")

            if level < cls.MIN_SKILL_LEVEL or level > cls.MAX_SKILL_LEVEL:
                raise InvalidArgumentError(
                    f"Skill '{name}' has invalid level: {level}. "
                    f"Skill levels must be between {cls.MIN_SKILL_LEVEL} and {cls.MAX_SKILL_LEVEL}.")

    def set_current_skills(self, tx, skills):
        selected_skills = []
        for skill_data in skills:
            # TODO: (sunil) Handle IntegrityError if multiple users add the same new skill at the same time
            skill = Skill.lookup_or_add(tx, skill_data.get('skill_id'), skill_data['name'])

            user_skill = UserCurrentSkill(level=skill_data['level'])
            user_skill.skill = skill
            selected_skills.append(user_skill)

        # TODO: (sunil) Need to lock the user here so no other thread can make updates

        existing_skill_ids = [skill.id for skill in self.current_skills]
        selected_skill_ids = [skill.id for skill in selected_skills]

        # Remove or update the existing skills
        for existing_skill in self.current_skills:
            if existing_skill.id not in selected_skill_ids:
                tx.delete(existing_skill)
                continue

            selected_skill = next(skill for skill in selected_skills if skill.id == existing_skill.id)
            existing_skill.level = selected_skill.level

        # Now add any new ones
        for selected_skill in selected_skills:
            if selected_skill.id not in existing_skill_ids:
                self.current_skills.append(selected_skill)

    def set_desired_skills(self, tx, skills):
        selected_skills = []
        for skill_data in skills:
            # TODO: (sunil) Handle IntegrityError if multiple users add the same new skill at the same time
            skill = Skill.lookup_or_add(tx, skill_data.get('skill_id'), skill_data['name'])

            user_desired_skill = UserDesiredSkill()
            user_desired_skill.skill = skill
            selected_skills.append(user_desired_skill)

        # TODO: (sunil) Need to lock the user here so no other thread can make updates

        existing_skill_ids = [skill.id for skill in self.desired_skills]
        selected_skill_ids = [skill.id for skill in selected_skills]

        # Remove any skill that is not in the new list
        for existing_skill in self.desired_skills:
            if existing_skill.id not in selected_skill_ids:
                tx.delete(existing_skill)

        # Now add any new ones
        for selected_skill in selected_skills:
            if selected_skill.id not in existing_skill_ids:
                self.desired_skills.append(selected_skill)

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

        def add_if_not_none(key, value):
            if value is not None:
                user[key] = value

        add_if_not_none('title', self.profile.get('title'))
        add_if_not_none('profile_picture_url', self.profile.get('profile_picture_url'))

        return user
