from datetime import datetime
import uuid

from flask import jsonify, request
from flask_cognito import current_cognito_jwt
from flask_smorest import Blueprint

from backend.common.http import make_no_content_response
from backend.common.exceptions import InvalidArgumentError, NotAllowedError
from backend.models.db import transaction
from backend.models.offer import (
    Offer, OfferStatus,
    OfferProposal, OfferProposalStatus, OfferProposalFilter
)
from backend.models.user import User
from backend.models.user_upload import UserUpload, UserUploadStatus
from backend.views.user_upload import UserUploadMixin
from backend.views.base import AuthenticatedAPIBase


blueprint = Blueprint('offer', __name__, url_prefix='/offers')
proposal_blueprint = Blueprint('offer_proposal', __name__, url_prefix='/proposals')


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


@blueprint.route('/<offer_id>/proposals')
class OfferProposalAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(offer_id):
        proposal_filter = OfferProposalFilter.lookup(request.args.get('filter'))

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            proposals = OfferProposal.search(
                tx,
                user,
                offer_id,
                proposal_filter=proposal_filter
            )
            proposals = [proposal.as_dict() for proposal in proposals]
        return jsonify(proposals)

    @staticmethod
    def post(offer_id):
        payload = request.json
        proposal_id = str(uuid.uuid4())
        now = datetime.utcnow()

        required_fields = {'name', 'overview_text'}
        missing_fields = required_fields - set(payload.keys())
        if missing_fields:
            raise InvalidArgumentError(f"Field: {', '.join(missing_fields)} is required.")

        with transaction() as tx:
            proposer_id = User.lookup(tx, current_cognito_jwt['sub'])
            offer = Offer.lookup(tx, offer_id)
            proposal = OfferProposal(
                id=proposal_id,
                name=payload.get('name'),
                proposer=proposer_id,
                offer_id=offer.id,
                status=OfferProposalStatus.NEW.value,
                created_at=now,
                last_updated_at=now
            )
            tx.add(proposal)

            proposal.update_details(payload)
            proposal_details = proposal.as_dict()

        return proposal_details


@proposal_blueprint.route('/<proposal_id>')
class OfferProposalByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(proposal_id):
        with transaction() as tx:
            proposal = OfferProposal.lookup(tx, proposal_id)
            return proposal.as_dict()

    @staticmethod
    def put(proposal_id):
        now = datetime.utcnow()

        with transaction() as tx:
            proposal = OfferProposal.lookup(tx, proposal_id)
            payload = request.json

            if payload.get('name'):
                proposal.name = payload['name']

            proposal.update_details(payload)

            if 'status' in payload:
                new_status = OfferProposalStatus.lookup(payload['status'])

                if proposal.status != new_status:
                    proposal.status = new_status.value

                    if new_status in [OfferProposalStatus.SELECTED, OfferProposalStatus.REJECTED]:
                        proposal.decided_at = now
                    if new_status in [OfferProposalStatus.COMPLETED, OfferProposalStatus.SUSPENDED]:
                        proposal.closed_at = now

            proposal.last_updated_at = now

        # Fetch the proposal again from the database so the updates made above are reflected in the response
        with transaction() as tx:
            proposal = OfferProposal.lookup(tx, proposal_id)
            proposal_details = proposal.as_dict()
        return proposal_details

    @staticmethod
    def delete(proposal_id):
        now = datetime.utcnow()

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            proposal = OfferProposal.lookup(tx, proposal_id)

            # For now, only the creator is allowed to delete the proposal
            if proposal.proposer_id != user.id:
                raise NotAllowedError(f"User '{user.id}' is not the creator of this proposal")
            proposal.status = OfferProposalStatus.DELETED.value
            proposal.last_updated_at = now
        return make_no_content_response()


@proposal_blueprint.route('/<proposal_id>/proposal_video')
class OfferProposalVideoAPI(AuthenticatedAPIBase, UserUploadMixin):
    @staticmethod
    def put(proposal_id):
        metadata = {
            'resource': 'proposal',
            'resource_id': proposal_id,
            'type': 'proposal_video',
        }
        return OfferProposalVideoAPI.create_user_upload(
            current_cognito_jwt['sub'], request.json['filename'], request.json['content_type'], 'proposals', metadata)


@proposal_blueprint.route('/<proposal_id>/proposal_video/<upload_id>')
class OfferProposalVideoByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(proposal_id, upload_id):
        status = UserUploadStatus.lookup(request.json['status'])
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            proposal = OfferProposal.lookup(tx, proposal_id)
            if status == UserUploadStatus.UPLOADED:
                proposal.overview_video_id = user_upload.id
                user_upload.status = status.value

        return {
            'status': user_upload.status,
        }

    @staticmethod
    def delete(proposal_id, upload_id):
        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            user_upload = UserUpload.lookup(tx, upload_id, user.customer_id)
            proposal = OfferProposal.lookup(tx, proposal_id)

            proposal.overview_video_id = None
            user_upload.status = UserUploadStatus.DELETED.value
        return make_no_content_response()


@proposal_blueprint.route('/<proposal_id>/offerer-feedback')
class OfferFeedbackAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(proposal_id):
        now = datetime.utcnow()

        with transaction() as tx:
            author = User.lookup(tx, current_cognito_jwt['sub'])
            proposal = OfferProposal.lookup(tx, proposal_id)

            if author.id != proposal.proposer.id:
                raise NotAllowedError(f"User '{author.id}' is not the proposal owner.")

            payload = request.json
            offerer_feedback_details = {}
            if 'comments' in payload:
                offerer_feedback_details['comments'] = payload['comments']

            if 'concerns' in payload:
                offerer_feedback_details['concerns'] = payload['concerns']

            if 'additional_comments' in payload:
                offerer_feedback_details['additional_comments'] = payload['additional_comments']

            proposal.offerer_feedback = offerer_feedback_details
            proposal.offerer_feedback_at = now
            proposal.last_updated_at = now

        with transaction() as tx:
            proposal = OfferProposal.lookup(tx, proposal_id)
            proposal_details = proposal.as_dict()
        return proposal_details


@proposal_blueprint.route('/<proposal_id>/proposer-feedback')
class ProposerFeedbackAPI(AuthenticatedAPIBase):
    @staticmethod
    def put(proposal_id):
        now = datetime.utcnow()

        with transaction() as tx:
            author = User.lookup(tx, current_cognito_jwt['sub'])
            proposal = OfferProposal.lookup(tx, proposal_id)

            if author.id != proposal.offer.offerer.id:
                raise NotAllowedError(f"User '{author.id}' is not the offer owner.")

            payload = request.json
            proposer_feedback_details = {}
            if 'comments' in payload:
                proposer_feedback_details['comments'] = payload['comments']

            if 'concerns' in payload:
                proposer_feedback_details['concerns'] = payload['concerns']

            if 'additional_comments' in payload:
                proposer_feedback_details['additional_comments'] = payload['additional_comments']

            proposal.proposer_feedback = proposer_feedback_details
            proposal.proposer_feedback_at = now
            proposal.last_updated_at = now

        with transaction() as tx:
            proposal = OfferProposal.lookup(tx, proposal_id)
            proposal_details = proposal.as_dict()
        return proposal_details
