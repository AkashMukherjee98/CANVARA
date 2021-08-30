from flask import jsonify

from backend.views.base import AuthenticatedAPIBase


class PerformerFeedbackAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id, performer_id):  # pylint: disable=unused-argument
        # TODO: (sunil) impement this
        return {}

    @staticmethod
    def post(post_id, performer_id):  # pylint: disable=unused-argument
        # TODO: (sunil) impement this
        return {}


class PosterFeedbackAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id):  # pylint: disable=unused-argument
        # TODO: (sunil) impement this
        return jsonify([])

    @staticmethod
    def post(post_id):  # pylint: disable=unused-argument
        # TODO: (sunil) impement this
        return {}
