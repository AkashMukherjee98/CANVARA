from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.http import make_no_content_response
from backend.common.exceptions import InvalidArgumentError, NotAllowedError
from backend.models.db import transaction
from backend.models.offer import Offer, OfferStatus
from backend.models.user import User
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('offer', __name__, url_prefix='/offers')


@blueprint.route('')
class OfferAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            offers = Offer.search(
                tx,
                user
            )
            offers = [offer.as_dict() for offer in offers]
        return jsonify(offers)

    @staticmethod
    def post():
        payload = request.json
        offer_id = str(uuid.uuid4())
        now = datetime.utcnow()

        required_fields = {'name', 'overview_text'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")

        with transaction() as tx:
            offerer_id = User.lookup(tx, current_cognito_jwt['sub'])

            offer = Offer(
                id=offer_id,
                name=payload.get('name'),
                offerer=offerer_id,
                status=OfferStatus.ACTIVE.value,
                created_at=now,
                last_updated_at=now
            )
            tx.add(offer)

            offer.update_details(payload)
            offer_details = offer.as_dict()

        return offer_details


@blueprint.route('/<offer_id>')
class OfferByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(offer_id):
        with transaction() as tx:
            offer = Offer.lookup(tx, offer_id)
            return offer.as_dict()

    @staticmethod
    def put(offer_id):
        now = datetime.utcnow()

        with transaction() as tx:
            offer = Offer.lookup(tx, offer_id)

            payload = request.json

            if payload.get('name'):
                offer.name = payload['name']

            offer.last_updated_at = now
            offer.update_details(payload)

        # Fetch the offer again from the database so the updates made above are reflected in the response
        with transaction() as tx:
            offer = Offer.lookup(tx, offer_id)
            offer_details = offer.as_dict()
        return offer_details

    @staticmethod
    def delete(offer_id):
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            offer = Offer.lookup(tx, offer_id)

            # For now, only the offerer is allowed to delete the offer
            if offer.offerer_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the creator of this offer")
            offer.status = OfferStatus.DELETED.value
            offer.last_updated_at = now
        return make_no_content_response()


@blueprint.route('/<offer_id>/offer_video')
class OfferVideoAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(offer_id):
        metadata = {
            'resource': 'offer',
            'resource_id': offer_id,
            'type': 'offer_video',
        }
        return OfferVideoAPI.create_user_upload(
            current_cognito_jwt['sub'], request.json['filename'], request.json['content_type'], 'offers', metadata)


@blueprint.route('/<offer_id>/offer_video/<upload_id>')
class OfferVideoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(offer_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            offer = Offer.lookup(tx, offer_id)
            if status == UserUploadStatus.UPLOADED:
                offer.overview_video_id = user_upload.id
                user_upload.status = status.value

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(offer_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            offer = Offer.lookup(tx, offer_id)

            offer.overview_video_id = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()
