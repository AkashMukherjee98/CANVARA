from datetime import datetime
import uuid

from sqlalchemy import and_, or_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError
from .db import ModelBase


class Skill(ModelBase):
    __tablename__ = 'skill'
    # TODO: (sunil) Remove internal_name, instead put a functional index on name, like location table

    DEFAULT_SEARCH_RESULTS_LIMIT = 20
    MAX_SEARCH_RESULTS_LIMIT = 50

    @classmethod
    def lookup(cls, tx, customer_id, skill_id=None, name=None, must_exist=True):  # pylint: disable=too-many-arguments
        if skill_id is None and name is None:
            raise InvalidArgumentError("Either skill id or name is required for lookup")

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
            internal_name = name.lower()
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
    def lookup_or_add(cls, tx, customer_id, skill_id=None, name=None):
        # Lookup the skill based on id or name, or add a new custom skill
        skill = Skill.lookup(tx, customer_id, skill_id=skill_id, name=name, must_exist=False)
        if skill is None:
            skill = Skill.add_custom_skill(name, customer_id)
        return skill

    @classmethod
    def search(cls, tx, customer_id, query=None, limit=None):
        if not limit:
            limit = cls.DEFAULT_SEARCH_RESULTS_LIMIT
        limit = min(limit, cls.MAX_SEARCH_RESULTS_LIMIT)

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


class SkillWithoutLevelMixin:
    @declared_attr
    def skill(self):
        return relationship("Skill")

    @property
    def id(self):
        return self.skill.id

    def as_dict(self):
        return self.skill.as_dict()

    @classmethod
    def update_skills(cls, tx, customer_id, existing_skills, skills, factory=None):  # pylint: disable=too-many-arguments
        # Caller can specify a factory method to create the table row
        # If it's not specified, just use the class constructor
        if factory is None:
            factory = cls

        selected_skills = []
        for skill_data in skills:
            # TODO: (sunil) Handle IntegrityError if multiple users add the same new skill at the same time
            skill = Skill.lookup_or_add(tx, customer_id, skill_id=skill_data.get('skill_id'), name=skill_data.get('name'))
            selected_skills.append(factory(skill=skill))

        existing_skill_ids = [skill.id for skill in existing_skills]
        selected_skill_ids = [skill.id for skill in selected_skills]

        # Remove any skill that is not in the new list
        skills_to_remove = [skill for skill in existing_skills if skill.id not in selected_skill_ids]
        for existing_skill in skills_to_remove:
            existing_skill.skill.usage_count -= 1
            tx.delete(existing_skill)
            existing_skills.remove(existing_skill)

        # Now add any new ones
        for selected_skill in selected_skills:
            if selected_skill.id not in existing_skill_ids:
                selected_skill.skill.usage_count += 1
                existing_skills.append(selected_skill)

    def matches(self, other):
        return isinstance(other, SkillWithoutLevelMixin) and self.id == other.id


class SkillWithLevelMixin(SkillWithoutLevelMixin):
    MIN_SKILL_LEVEL = 1
    MAX_SKILL_LEVEL = 100
    SKILL_LEVEL_MATCH_RANGE = 20

    def as_dict(self):
        details = self.skill.as_dict()
        details['level'] = self.level
        if hasattr(self, 'is_expert'):
            details['is_expert'] = False if self.is_expert is None else self.is_expert
        return details

    @classmethod
    def validate_skill_level(cls, name, level):
        if level is None:
            raise InvalidArgumentError(f"Level is required for skill '{name}'.")

        if level < cls.MIN_SKILL_LEVEL or level > cls.MAX_SKILL_LEVEL:
            raise InvalidArgumentError(
                f"Skill '{name}' has invalid level: {level}. "
                f"Skill levels must be between {cls.MIN_SKILL_LEVEL} and {cls.MAX_SKILL_LEVEL}.")

    @classmethod
    def update_skills(cls, tx, customer_id, existing_skills, skills, factory=None):  # pylint: disable=too-many-arguments
        # Caller can specify a factory method to create the table row
        # If it's not specified, just use the class constructor
        if factory is None:
            factory = cls

        selected_skills = []
        for skill_data in skills:
            # TODO: (sunil) Handle IntegrityError if multiple users add the same new skill at the same time
            skill = Skill.lookup_or_add(tx, customer_id, skill_id=skill_data.get('skill_id'), name=skill_data.get('name'))
            if 'is_expert' in skill_data:
                selected_skills.append(factory(level=skill_data['level'], is_expert=skill_data['is_expert'], skill=skill))
            else:
                selected_skills.append(factory(level=skill_data['level'], skill=skill))

        existing_skill_ids = [skill.id for skill in existing_skills]
        selected_skill_ids = [skill.id for skill in selected_skills]

        # Remove any skill that is not in the new list
        skills_to_remove = [skill for skill in existing_skills if skill.id not in selected_skill_ids]
        for existing_skill in skills_to_remove:
            existing_skill.skill.usage_count -= 1
            tx.delete(existing_skill)
            existing_skills.remove(existing_skill)

        # Update level for existing skills
        for existing_skill in existing_skills:
            selected_skill = next(skill for skill in selected_skills if skill.id == existing_skill.id)
            existing_skill.level = selected_skill.level

        # Now add any new ones
        for selected_skill in selected_skills:
            if selected_skill.id not in existing_skill_ids:
                selected_skill.skill.usage_count += 1
                existing_skills.append(selected_skill)

    def matches(self, other):
        # Instead of requiring an exact match, another skill is considered a 'match' if:
        # - it has a higher level, or
        # - it has level within SKILL_LEVEL_MATCH_RANGE of this skill
        return (
            isinstance(other, SkillWithLevelMixin) and
            self.id == other.id and
            other.level >= (self.level - self.SKILL_LEVEL_MATCH_RANGE)
        )
