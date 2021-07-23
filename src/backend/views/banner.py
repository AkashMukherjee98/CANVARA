import random

from flask import jsonify
from flask_cognito import current_cognito_jwt

from backend.models.db import transaction
from backend.models.user import User
from backend.views.base import AuthenticatedAPIBase


class BannerAPI(AuthenticatedAPIBase):
    @staticmethod
    def get():
        banners = [{
            'type': 'message',
            'data': {
                'title': 'Knock, Knock!',
                'subtitle': "It's me, Opportunity"
            },
        }]

        with transaction() as tx:
            user = User.lookup(tx, current_cognito_jwt['sub'])
            random.seed(user.id)

            banners.append({
                'type': 'progress',
                'data': {
                    'title': 'Finish your profile',
                    'percent': random.randrange(30, 91)  # TODO: (sunil) implement this
                },
            })

        banners.append({
            'type': 'message',
            'data': {
                'title': 'Project Athena needs your help!',
            }
        })

        return jsonify(banners)
