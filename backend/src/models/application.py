from enum import Enum

from pynamodb.attributes import UnicodeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
import pynamodb.exceptions
import pynamodb.models
from common.exceptions import DoesNotExistError, InvalidArgumentError

class ApplicantIdIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'applicant_id-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()

    applicant_id = UnicodeAttribute(hash_key=True)
    post_id = UnicodeAttribute(range_key=True)

class ApplicationIdIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'application_id-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()

    application_id = UnicodeAttribute(hash_key=True)

class Application(pynamodb.models.Model):
    class Meta:
        table_name = 'application'
        region = 'us-west-2'

    class Status(Enum):
        NEW = 'new'
        APPROVED = 'approved'
        DENIED = 'denied'
        REJECTED = 'rejected'
        SHORTLISTED = 'shortlisted'
        SELECTED = 'selected'

    post_id = UnicodeAttribute(hash_key=True)
    applicant_id = UnicodeAttribute(range_key=True)
    application_id = UnicodeAttribute()
    description = UnicodeAttribute()

    # TODO: (sunil) Convert this to enum attribute
    status = UnicodeAttribute()

    # Secondary Indexes
    applicant_id_index = ApplicantIdIndex()
    application_id_index = ApplicationIdIndex()

    @classmethod
    def lookup(cls, application_id, must_exist=True):
        try:
            return next(Application.application_id_index.query(application_id))
        except StopIteration:
            if must_exist:
                raise DoesNotExistError(f"Application '{application_id}' does not exist")
        return None

    @classmethod
    def lookup_multiple(cls, post_id=None, applicant_id=None):
        applications = []
        if post_id is not None:
            applications = Application.query(post_id)
        elif applicant_id is not None:
            applications = Application.applicant_id_index.query(applicant_id)

        return [application.as_dict() for application in applications]

    @classmethod
    def validate_status(cls, status):
        try:
            _ = Application.Status(status).value
        except ValueError:
            raise InvalidArgumentError(f"Invalid application status: {status}")

    def as_dict(self):
        return {
            'post_id': self.post_id,
            'applicant_id': self.applicant_id,
            'application_id': self.application_id,
            'description': self.description,
            'status': self.status,
        }
