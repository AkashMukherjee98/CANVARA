from datetime import datetime

from flask import jsonify, request
from flask_smorest import Blueprint

from backend.models.db import transaction
from backend.models.performer import Performer, PerformerStatus
from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('performer', __name__, url_prefix='/posts/<post_id>/performers')


@blueprint.route('')
class PerformerAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id):
        with transaction() as tx:
            performers = Performer.lookup_by_post(tx, post_id)
        return jsonify([performer.as_dict() for performer in performers])


@blueprint.route('/<performer_id>')
class PerformerByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id, performer_id):
        with transaction() as tx:
            performer = Performer.lookup(tx, post_id, performer_id)
        return performer.as_dict()

    @staticmethod
    def put(post_id, performer_id):
        with transaction() as tx:
            performer = Performer.lookup(tx, post_id, performer_id)

            # TODO: (sunil) enforce correct state transitions
            if 'status' in request.json:
                performer.status = PerformerStatus.lookup(request.json['status']).value

            performer.last_updated_at = datetime.utcnow()
        return performer.as_dict()
