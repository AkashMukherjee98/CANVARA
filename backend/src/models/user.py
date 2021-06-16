import copy

from sqlalchemy.orm import relationship

from common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase

class User(ModelBase):
    # Note: 'user' is a reserved keyword in PostgreSQL so we use 'canvara_user' instead
    __table__ = db.metadata.tables['canvara_user']

    customer = relationship("Customer", back_populates="users")
    posts = relationship("Post", back_populates="owner")
    applications = relationship("Application", back_populates="applicant")
    product_preferences = relationship("ProductPreference", secondary=db.metadata.tables['user_product_preference'])

    @classmethod
    def lookup(cls, tx, id):
        user = tx.get(cls, id)
        if user is None:
            raise DoesNotExistError(f"User '{id}' does not exist")
        return user

    @classmethod
    def validate_skills(cls, skills):
        skill_names = set()
        for skill in skills:
            name, level = skill['name'], skill['level']
            if name in skill_names:
                raise InvalidArgumentError(f"Multiple entries found for skill '{name}'.")
            skill_names.add(name)

            if level < 1 or level > 3:
                raise InvalidArgumentError(
                    f"Skill '{name}' has invalid level: {level}. Skill levels must be between 1 and 3.")

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

        def add_if_not_none(key, value):
            if value is not None:
                user[key] = value

        add_if_not_none('title', self.profile.get('title'))
        add_if_not_none('profile_picture_url', self.profile.get('profile_picture_url'))

        if self.profile.get('skills'):
            user['skills'] = self.profile['skills']

        if self.profile.get('skills_to_acquire'):
            user['skills_to_acquire'] = self.profile['skills_to_acquire']

        return user
