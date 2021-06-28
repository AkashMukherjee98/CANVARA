from datetime import datetime
import uuid

from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase


class Skill(ModelBase):
    __table__ = db.metadata.tables['skill']

    @classmethod
    def lookup(cls, tx, customer_id, skill_id=None, name=None, must_exist=True):
        if skill_id is None and name is None:
            raise InvalidArgumentError("Either skill id or name is required for lookup")

        internal_name = name.lower()
        skill = None
        if skill_id is not None:
            # TODO: (sunil) if name was also given, make sure it matches
            skill = tx.get(cls, skill_id)
            if skill is None and must_exist:
                raise DoesNotExistError(f"Skill '{skill_id}' does not exist")
        else:
            # Search for both global and customer-specific skills
            # It's possible that we have both a global and a customer-specific skill with the same name
            # In that case, pick the global skill

            # Note: This query will return a maximum of two rows, so fetching both and filtering in Python
            # is okay. The amount of data fetched will still be small, and the query is much simpler.
            skills_query = tx.query(Skill).where(
                and_(
                    Skill.internal_name == internal_name,
                    or_(
                        Skill.customer_id == None,
                        Skill.customer_id == customer_id)))
            for skill in skills_query:
                if skill.customer_id is None:
                    # We found a global skill. Stop looking!
                    break

            if skill is None and must_exist:
                raise DoesNotExistError(f"Skill '{name}' does not exist")
        return skill

    @classmethod
    def add_custom_skill(cls, name, customer_id):
        return Skill(
            id=str(uuid.uuid4()),
            internal_name=name.lower(),
            display_name=name,
            customer_id=customer_id,
            created_at=datetime.utcnow(),
            usage_count=0)

    @classmethod
    def search(cls, tx, query=None):
        skills = tx.query(Skill).where(Skill.name.startswith(query, autoescape=True))
        return [skill.as_dict() for skill in skills]

    def as_dict(self):
        return {
            'skill_id': self.id,
            'name': self.display_name
        }
