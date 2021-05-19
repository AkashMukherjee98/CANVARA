from flask import Flask
from flask_cognito import CognitoAuth

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

import views.customer
import views.user
import views.post
