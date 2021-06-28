from datetime import datetime
import uuid

from sqlalchemy import and_, or_

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import db, ModelBase


class Skill(ModelBase):
    __table__ = db.metadata.tables['skill']

    @classmethod
    def lookup(cls, tx, customer_id, skill_id=None, name=None, must_exist=True):  # pylint: disable=too-many-arguments
        if skill_id is None and name is None:
            raise InvalidArgumentError("Either skill id or name is required for lookup")

        internal_name = name.lower()
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
                        Skill.customer_id.is_(None),
                        Skill.customer_id == customer_id)))
            skill = None
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
    def search(cls, tx, customer_id, query=None, limit=10):
        customer_id_clause = or_(
            Skill.customer_id.is_(None),
            Skill.customer_id == customer_id)

        if not query:
            # If no query was given, return the overall most used skills
            skills_query = tx.query(Skill).where(customer_id_clause)
        else:
            # If a query was given, return the most used skills that contain that query somewhere in the name
            # TODO: (sunil) Improve this by adding stemming etc.
            query = query.lower()
            skills_query = tx.query(Skill).where(
                and_(
                    Skill.internal_name.like(f'%{query}%'),
                    customer_id_clause))

        # It's possible to have a global and a custom skill by the same name
        # So fetch 2x the number of results we want to return, and then dedupe
        # This can also be done entirely in SQL, but that results in a much more complex query
        skills_query = skills_query.order_by(Skill.usage_count.desc()).limit(2*limit)
        skills = []
        skill_names_seen = set()
        for skill in skills_query:
            if skill.internal_name in skill_names_seen:
                continue
            skill_names_seen.add(skill.internal_name)
            skills.append(skill)
        return [skill.as_dict() for skill in skills[:limit]]

    def as_dict(self):
        return {
            'skill_id': self.id,
            'name': self.display_name
        }
