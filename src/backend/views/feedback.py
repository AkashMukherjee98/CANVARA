from flask import jsonify

from backend.views.base import AuthenticatedAPIBase


class FeedbackAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id):  # pylint: disable=unused-argument
        # TODO: (sunil) impement this
        return jsonify([])

    @staticmethod
    def post(post_id):  # pylint: disable=unused-argument
        # TODO: (sunil) impement this
        return {}
