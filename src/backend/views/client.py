from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.http import make_no_content_response
from backend.common.exceptions import InvalidArgumentError

from backend.models.db import transaction
from backend.models.user import User
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.models.client import Client, ClientStatus, ClientStatusFilter

from backend.views.base import AuthenticatedAPIBase
from backend.views.user_upload import UserUploadMixin


blueprint = Blueprint('client', __name__, url_prefix='/clients')


@blueprint.route('')
class ClientAPI(AuthenticatedAPIBase):
    @staticmethod
    def post():
        payload = request.json
        client_id = str(uuid.uuid4())
        now = datetime.utcnow()

        required_fields = {'name'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])

            client = Client(
                id=client_id,
                customer_id=user.customer_id,
                name=payload.get('name'),
                status=ClientStatus.ACTIVE.value,
                created_at=now,
                last_updated_at=now
            )
            tx.add(client)

            client_details = client.as_dict()

        return client_details

    @staticmethod
    def get():
        status = ClientStatusFilter.lookup(request.args.get('status'))

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            clients = Client.search(
                tx,
                user.customer_id,
                status=status
            )
            clients = [client.as_dict() for client in clients]
        return jsonify(clients)


@blueprint.route('/<client_id>')
class ClientByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(client_id):
        payload = request.json
        now = datetime.utcnow()

        with transaction() as tx:
            client = Client.lookup(tx, client_id)

            if payload.get('name'):
                client.name = payload['name']

            if payload.get('status'):
                new_status = ClientStatus.lookup(payload['status'])
                if client.status != new_status:
                    client.status = new_status.value

            client.last_updated_at = now

        with transaction() as tx:
            client = Client.lookup(tx, client_id)
            client_details = client.as_dict()
        return client_details


@blueprint.route('/<client_id>/client_logo')
class ClientLogoAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(client_id):
        metadata = {
            'resource': 'client',
            'resource_id': client_id,
            'type': 'client_logo',
        }
        return ClientLogoAPI.create_user_upload(
            current_cognito_jwt['sub'], request.json['filename'], request.json['content_type'], 'clients', metadata)


@blueprint.route('/<client_id>/client_logo/<upload_id>')
class ClientLogoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(client_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            client = Client.lookup(tx, client_id)
            if status == UserUploadStatus.UPLOADED:
                client.logo_id = user_upload.id
                user_upload.status = status.value

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(client_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            client = Client.lookup(tx, client_id)

            client.logo_id = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()
