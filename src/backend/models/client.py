from enum import Enum

from sqlalchemy import and_
from sqlalchemy.orm import relationship

from backend.common.exceptions import DoesNotExistError, InvalidArgumentError

from .db import ModelBase
from .user_upload import UserUpload


class ClientStatus(Enum):
    ACTIVE = 'active'
    DELETED = 'deleted'

    @classmethod
    def lookup(cls, client_status):
        if client_status is None:
            return None

        try:
            return ClientStatus(client_status.lower())
        except ValueError as ex:
            raise InvalidArgumentError(f"Unsupported status : {client_status}.") from ex


class Client(ModelBase):
    __tablename__ = 'client'

    client_logo = relationship(UserUpload, foreign_keys="[Client.logo_id]")
    projects = relationship("Project", back_populates="client")
    details = None

    def as_dict(self, return_keys=all):  # if return_keys=all return everything, if any key(s) specified then return those only
        client = {
            'client_id': self.id,
            'name': self.name
        }

        def add_if_required(key, value):
            if (return_keys is all or key in return_keys) and value is not None:
                client[key] = value

        add_if_required(
            'client_logo', self.client_logo.as_dict(method='get') if self.client_logo else None)

        return client

    @classmethod
    def lookup(cls, tx, client_id):
        client = tx.query(cls).where(and_(
            cls.id == client_id,
            cls.status != ClientStatus.DELETED.value
        ))

        client = client.one_or_none()
        if client is None:
            raise DoesNotExistError(f"Client '{client_id}' does not exist")

        return client

    @classmethod
    def search(cls, tx, customer_id):
        clients = tx.query(cls).where(and_(
            cls.customer_id == customer_id,
            cls.status == ClientStatus.ACTIVE.value
        ))

        return clients
