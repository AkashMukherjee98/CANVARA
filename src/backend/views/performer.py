from flask import jsonify

from backend.views.base import AuthenticatedAPIBase


class PerformerAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id):  # pylint: disable=unused-argument
        # TODO: (sunil) impement this
        return jsonify([])


class PerformerByIdAPI(AuthenticatedAPIBase):
    @staticmethod
    def get(post_id, performer_id):  # pylint: disable=unused-argument
        # TODO: (sunil) impement this
        return {}

    @staticmethod
    def put(post_id, performer_id):  # pylint: disable=unused-argument
        # TODO: (sunil) impement this
        return {}
