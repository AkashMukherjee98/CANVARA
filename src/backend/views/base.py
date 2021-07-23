from flask.views import MethodView
from flask_cognito import cognito_auth_required

from backend.common.logging import api_trace


class AuthenticatedAPIBase(MethodView):
    decorators = [api_trace, cognito_auth_required]
