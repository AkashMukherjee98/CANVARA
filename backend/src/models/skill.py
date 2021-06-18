import uuid

from common.exceptions import DoesNotExistError

from .db import db, ModelBase

class Skill(ModelBase):
    __table__ = db.metadata.tables['skill']

    @classmethod
    def lookup(cls, tx, id):
        skill = tx.get(cls, id)
        if skill is None:
            raise DoesNotExistError(f"Skill '{id}' does not exist")
        return skill

    @classmethod
    def lookup_or_add(cls, tx, id, name):
        if id is not None:
            return Skill.lookup(tx, id)

        # If no id was given, add this as a new custom skill
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
