from flask import Flask
from flask_cognito import CognitoAuth
from flask_cors import CORS


def create_app():
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

    from backend.common.exceptions import APP_ERROR_HANDLERS  # pylint: disable=import-outside-toplevel
    for exception_type, exception_handler in APP_ERROR_HANDLERS.items():
        app.register_error_handler(exception_type, exception_handler)

    with app.app_context():
        # pylint: disable=import-outside-toplevel, unused-import
        import backend.views.customer
        import backend.views.user
        import backend.views.post
        import backend.views.application
        import backend.views.onboarding
        import backend.views.skill  # noqa: F401
        # pylint: enable=import-outside-toplevel, unused-import

    return app
