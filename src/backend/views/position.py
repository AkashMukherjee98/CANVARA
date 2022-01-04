from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.http import make_no_content_response
from backend.common.exceptions import InvalidArgumentError
from backend.models.db import transaction
from backend.models.location import Location
from backend.models.position import Position, PositionStatus, PositionRoleType
from backend.models.user import User
from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('position', __name__, url_prefix='/positions')


@blueprint.route('')
class PositionAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            # This is the user making the request, for authorization purposes
            user = User.lookup(tx, current_cognito_jwt['sub'])
            positions = Position.search(
                tx,
                user
            )
            positions = [position.as_dict() for position in positions]
        return jsonify(positions)

    @staticmethod
    def post():
        payload = request.json
        # Generate a unique id for this position
        position_id = str(uuid.uuid4())

        now = datetime.utcnow()

        required_fields = {
            'manager_id', 'location_id', 'role_type', 'role', 'description', 'pay_minimum', 'pay_maximum', 'pay_currency'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")

        roletype = PositionRoleType.validate_and_return_role_type(payload['role_type'])

        with transaction() as tx:
            hiring_manager = User.lookup(tx, payload['manager_id'])
            location = Location.lookup(tx, payload['location_id'])

            Position.validate_pay_range(payload['pay_currency'], payload['pay_minimum'], payload['pay_maximum'])
            pay_currency = payload['pay_currency']
            pay_minimum = payload['pay_minimum']
            pay_maximum = payload['pay_maximum']

            position = Position(
                id=position_id,
                hiring_manager=hiring_manager,
                role=payload.get('role'),
                role_type=roletype,
                department=payload['department'],
                pay_currency=pay_currency,
                pay_minimum=pay_minimum,
                pay_maximum=pay_maximum,
                location=location,
                status=PositionStatus.ACTIVE.value,
                created_at=now,
                last_updated_at=now
            )
            position.update_details(payload)
            tx.add(position)

            position_details = position.as_dict()

        return position_details


@blueprint.route('/<position_id>')
class PositionByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(position_id):
        with transaction() as tx:
            position = Position.lookup(tx, position_id)
            return position.as_dict()

    @staticmethod
    def put(position_id):
        now = datetime.utcnow()

        with transaction() as tx:
            position = Position.lookup(tx, position_id)

            payload = request.json

            if payload.get('manager_id'):
                position.hiring_manager = User.lookup(tx, payload['manager_id'])

            if payload.get('role'):
                position.role = payload['role']

            if payload.get('role_type'):
                position.role_type = PositionRoleType.validate_and_return_role_type(payload['role_type'])

            if payload.get('department'):
                position.department = payload['department']

            Position.validate_pay_range(
                payload['pay_currency'] if 'pay_currency' in payload else position.pay_currency,
                payload['pay_minimum'] if 'pay_minimum' in payload else position.pay_minimum,
                payload['pay_maximum'] if 'pay_maximum' in payload else position.pay_maximum
            )
            if payload.get('pay_currency'):
                position.pay_currency = payload['pay_currency']
            if payload.get('pay_minimum'):
                position.pay_minimum = payload['pay_minimum']
            if payload.get('pay_maximum'):
                position.pay_maximum = payload['pay_maximum']

            if payload.get('location_id'):
                position.location = Location.lookup(tx, payload['location_id'])

            position.last_updated_at = now
            position.update_details(payload)

        # Fetch the position again to get updated response
        with transaction() as tx:
            position = Position.lookup(tx, position_id)
            position_details = position.as_dict()
        return position_details

    @staticmethod
    def delete(position_id):
        now = datetime.utcnow()

        with transaction() as tx:
            position = Position.lookup(tx, position_id)

            # TODO: (santanu) System account can delete a position

            position.status = PositionStatus.DELETED.value
            position.last_updated_at = now
        return make_no_content_response()
