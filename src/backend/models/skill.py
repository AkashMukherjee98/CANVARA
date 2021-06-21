import uuid

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError

from .db import db, ModelBase

class Skill(ModelBase):
    __table__ = db.metadata.tables['skill']

    @classmethod
    def lookup(cls, tx, skill_id=None, name=None, must_exist=True):
        if skill_id is None and name is None:
            raise InvalidArgumentError("Either skill id or name is required for lookup")

        if skill_id is not None:
            # TODO: (sunil) if name was also given, make sure it matches
            skill = tx.get(cls, skill_id)
            if skill is None and must_exist:
                raise DoesNotExistError(f"Skill '{skill_id}' does not exist")
        else:
            skill = tx.query(Skill).where(Skill.name.ilike(name)).first()
            if skill is None and must_exist:
                raise DoesNotExistError(f"Skill '{name}' does not exist")
        return skill

    @classmethod
    def add_custom_skill(cls, name):
        return Skill(id=str(uuid.uuid4()), name=name, is_custom=True)

    @classmethod
    def search(cls, tx, query=None):
        skills = tx.query(Skill).where(Skill.name.startswith(query, autoescape=True))
        return [skill.as_dict() for skill in skills]

    def as_dict(self):
        return {
            'skill_id': self.id,
            'name': self.name,
            'is_custom': self.is_custom if self.is_custom is not None else False
        }
