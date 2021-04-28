from pynamodb.attributes import ListAttribute, MapAttribute, NumberAttribute, UnicodeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
import pynamodb.exceptions
import pynamodb.models
from common.exceptions import DoesNotExistError, InvalidArgumentError

class UserIdIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'user_id-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()

    user_id = UnicodeAttribute(hash_key=True)

class UserSkill(MapAttribute):
    name = UnicodeAttribute()
    level = NumberAttribute(default=1)

class UserProfile(MapAttribute):
    name = UnicodeAttribute()
    title = UnicodeAttribute(null=True)
    picture_url = UnicodeAttribute(null=True)
    skills = ListAttribute(null=True, of=UserSkill)
    skills_to_acquire = ListAttribute(null=True, of=UserSkill)

class User(pynamodb.models.Model):
    class Meta:
        table_name = 'user'
        region = 'us-west-2'

    customer_id = UnicodeAttribute(hash_key=True)
    user_id = UnicodeAttribute(range_key=True)
    profile = UserProfile(default={})
    user_id_index = UserIdIndex()

    @classmethod
    def lookup(cls, user_id, customer_id=None):
        if customer_id is None:
            try:
                return next(User.user_id_index.query(user_id))
            except StopIteration:
                raise DoesNotExistError(f"User '{user_id}' does not exist")

        try:
            return User.get(customer_id, user_id)
        except pynamodb.exceptions.DoesNotExist:
            raise DoesNotExistError(f"User '{user_id}' does not exist")

    @classmethod
    def exists(cls, user_id, customer_id=None):
        if customer_id is None:
            return User.user_id_index.count(user_id) > 0
        return User.count(customer_id, user_id) > 0

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

    def as_dict(self):
        user = {
            'customer_id': self.customer_id,
            'user_id': self.user_id,
            'name': self.profile.name,
        }

        def add_if_not_none(key, value):
            if value is not None:
                user[key] = value

        profile = self.profile.as_dict()
        add_if_not_none('title', profile.get('title'))
        add_if_not_none('profile_picture_url', profile.get('picture_url'))

        # TODO: (sunil) See how to automatically serialize the list correctly
        serialize_skills = lambda skills: [s.as_dict() if isinstance(s, MapAttribute) else s for s in skills]
        if profile.get('skills'):
            user['skills'] = serialize_skills(profile['skills'])

        if profile.get('skills_to_acquire'):
            user['skills_to_acquire'] = serialize_skills(profile['skills_to_acquire'])

        return user
