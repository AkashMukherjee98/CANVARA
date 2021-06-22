from flask import Flask
from flask_cognito import CognitoAuth
from flask_cors import CORS
import backend.common.exceptions

app = Flask(__name__)

app.config.update({
    'COGNITO_REGION': 'us-west-2',
    'COGNITO_USERPOOL_ID': 'us-west-2_WXlSvui2Y',
    'COGNITO_APP_CLIENT_ID': '4bqvh8quoqlvdrsi0rl4s5h3mt',
    'COGNITO_CHECK_TOKEN_EXPIRATION': True,
    'COGNITO_JWT_HEADER_NAME': 'Authorization',
    'COGNITO_JWT_HEADER_PREFIX': 'Bearer',
})

CognitoAuth(app)
CORS(app)

for exception_type, exception_handler in backend.common.exceptions.APP_ERROR_HANDLERS.items():
    app.register_error_handler(exception_type, exception_handler)

import backend.views.customer
import backend.views.user
import backend.views.post
import backend.views.application
import backend.views.onboarding
import backend.views.skill
