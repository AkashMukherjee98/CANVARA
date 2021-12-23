from datetime import datetime
import uuid
from psycopg2.extras import NumericRange

from flask import jsonify, request
from flask_cognito import current_cognito_jwt

from backend.common.http import make_no_content_response
from backend.common.exceptions import InvalidArgumentError, NotAllowedError
from backend.models.db import transaction
from backend.models.location import Location
from backend.models.position import Position, PositionStatus, PositionRoleType
from backend.models.user import User
from backend.views.base import AuthenticatedAPIBase


class PositionAPI(AuthenticatedAPIBase):

    @staticmethod
    def get(position_id=None):
        if position_id is None:
            return PositionAPI.__list_positions()
        return PositionAPI.__get_position(position_id)

    @staticmethod
    def __list_positions():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            positions = Position.search(
                tx,
                user
            )
            positions = [position.as_dict() for position in positions]
        return jsonify(positions)

    @staticmethod
    def __get_position(position_id):
        with transaction() as tx:
            position = Position.lookup(tx, position_id)
            return position.as_dict()

    @staticmethod
    def post():
        payload = request.json
        # Generate a unique id for this position
        position_id = str(uuid.uuid4())

        now = datetime.utcnow()

        required_fields = {'location_id', 'role_type', 'role', 'department', 'description'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")

        roletype = PositionRoleType.validate_and_return_role_type(payload['role_type'])

        with transaction() as tx:
            hiring_manager = User.lookup(tx, payload['manager_id']) \
                if 'manager_id' in payload and payload['manager_id'] else User.lookup(tx, current_cognito_jwt['sub'])
            location = Location.lookup(tx, payload['location_id'])
            pay_range = Position.validate_pay_range(NumericRange(payload['pay_minimum'], payload['pay_maximum']))

            position = Position(
                id=position_id,
                hiring_manager=hiring_manager,
                role=payload.get('role'),
                role_type=roletype,
                department=payload['department'],
                pay_range=pay_range,
                location=location,
                status=PositionStatus.ACTIVE.value,
                created_at=now,
                last_updated_at=now
            )
            position.update_details(payload)
            tx.add(position)

            position_details = position.as_dict()

        return position_details

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

            if (payload.get('pay_minimum') and payload.get('pay_maximum')):
                position.pay_range = Position.validate_pay_range(NumericRange(payload['pay_minimum'], payload['pay_maximum']))

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
            user = User.lookup(tx, current_cognito_jwt['sub'])
            position = Position.lookup(tx, position_id)

            # For now, only the hiring manager is allowed to delete the position
            if position.manager_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not a hiring manager")

            position.status = PositionStatus.DELETED.value
            position.last_updated_at = now
        return make_no_content_response()
