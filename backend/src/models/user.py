import copy

from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import update

from common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase
from .skill import Skill

class UserSkill(ModelBase):
    __table__ = db.metadata.tables['user_skill']
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
    skills = relationship("UserSkill")
    desired_skills = relationship("UserDesiredSkill")

    MIN_SKILL_LEVEL = 1
    MAX_SKILL_LEVEL = 10

    @classmethod
    def lookup(cls, tx, id):
        user = tx.get(cls, id)
        if user is None:
            raise DoesNotExistError(f"User '{id}' does not exist")
        return user

    @classmethod
    def validate_skills(cls, skills):
        skill_names_seen = set()
        for skill in skills:
            # Make sure there are no duplicate entries
            name = skill['name']
            if name in skill_names_seen:
                raise InvalidArgumentError(f"Multiple entries found for skill '{name}'.")
            skill_names_seen.add(name)

            # Validate the level if it's specified
            level = skill.get('level')
            if level is None:
                continue

            if level < cls.MIN_SKILL_LEVEL or level > cls.MAX_SKILL_LEVEL:
                raise InvalidArgumentError(
                    f"Skill '{name}' has invalid level: {level}. "
                    f"Skill levels must be between {cls.MIN_SKILL_LEVEL} and {cls.MAX_SKILL_LEVEL}.")

    def set_skills(self, tx, skills):
        selected_skills = []
        for skill_data in skills:
            # TODO: (sunil) Handle IntegrityError if multiple users add the same new skill at the same time
            skill = Skill.lookup_or_add(tx, skill_data.get('skill_id'), skill_data['name'])

            user_skill = UserSkill(level=skill_data['level'])
            user_skill.skill = skill
            selected_skills.append(user_skill)

        # TODO: (sunil) Need to lock the user here so no other thread can make updates

        existing_skill_ids = [skill.id for skill in self.skills]
        selected_skill_ids = [skill.id for skill in selected_skills]

        # Remove or update the existing skills
        for existing_skill in self.skills:
            if existing_skill.id not in selected_skill_ids:
                tx.delete(existing_skill)
                continue

            selected_skill = next(skill for skill in selected_skills if skill.id == existing_skill.id)
            existing_skill.level = selected_skill.level

        # Now add any new ones
        for selected_skill in selected_skills:
            if selected_skill.id not in existing_skill_ids:
                self.skills.append(selected_skill)

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
        user['skills'] = [skill.as_dict() for skill in self.skills]
        user['desired_skills'] = [skill.as_dict() for skill in self.desired_skills]

        def add_if_not_none(key, value):
            if value is not None:
                user[key] = value

        add_if_not_none('title', self.profile.get('title'))
        add_if_not_none('profile_picture_url', self.profile.get('profile_picture_url'))

        return user
