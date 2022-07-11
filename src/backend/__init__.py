import os

from flask import Flask
from flask_cognito import CognitoAuth
from flask_cors import CORS
from flask_smorest import Api


API_TITLE = 'Canvara Backend API'
API_VERSION = '0.43.0'
OPENAPI_VERSION = '3.0.0'


def create_app():  # pylint: disable=too-many-locals, disable=too-many-statements
    import backend.common.logging  # pylint: disable=import-outside-toplevel
    backend.common.logging.initialize_flask_logging()

    app = Flask(__name__)

    # If we're running under gunicorn, and configure logging to use gunicorn's logger
    if os.environ.get('SERVER_SOFTWARE', '').startswith('gunicorn/'):
        backend.common.logging.initialize_gunicorn_logging(app)

    # TODO: (sunil) move these env variables into config.py, remove config yaml file and use env variables instead
    app.config.update({
        'COGNITO_REGION': os.environ['COGNITO_REGION'],
        'COGNITO_USERPOOL_ID': os.environ['COGNITO_USERPOOL_ID'],
        'COGNITO_APP_CLIENT_ID': os.environ['COGNITO_APP_CLIENT_ID'],
        'COGNITO_CHECK_TOKEN_EXPIRATION': True,
        'COGNITO_JWT_HEADER_NAME': 'Authorization',
        'COGNITO_JWT_HEADER_PREFIX': 'Bearer',
    })

    CognitoAuth(app)
    CORS(app)
    api = Api(app, spec_kwargs={
        'title': API_TITLE,
        'version': API_VERSION,
        'openapi_version': OPENAPI_VERSION,
    })

    from backend.common.exceptions import APP_ERROR_HANDLERS  # pylint: disable=import-outside-toplevel
    for exception_type, exception_handler in APP_ERROR_HANDLERS.items():
        app.register_error_handler(exception_type, exception_handler)

    from backend.models.db import CanvaraDB  # pylint: disable=import-outside-toplevel
    CanvaraDB.init_db()

    # pylint: disable=import-outside-toplevel
    from .views.marketplace import blueprint as marketplace_blueprint
    from .views.activities import blueprint as activities_blueprint
    from .views.activities import blueprint_myactivities as myactivities_blueprint
    from .views.application import blueprint as application_blueprint, post_application_blueprint
    from .views.banner import blueprint as banner_blueprint
    from .views.community import blueprint as community_blueprint
    from .views.customer import blueprint as customer_blueprint
    from .views.event import blueprint as event_blueprint
    from .views.feedback import blueprint as feedback_blueprint
    from .views.match import blueprint as match_blueprint
    from .views.notification import blueprint as notification_blueprint
    from .views.offer import blueprint as offer_blueprint, proposal_blueprint
    from .views.onboarding import blueprint as onboarding_blueprint
    from .views.position import blueprint as position_blueprint
    from .views.performer import blueprint as performer_blueprint
    from .views.post import blueprint as post_blueprint, language_blueprint, location_blueprint, post_type_blueprint
    from .views.skill import blueprint as skill_blueprint
    from .views.user import blueprint as user_blueprint, customer_user_blueprint
    from .views.backgroundpicture import blueprint as backgroundpicture_blueprint
    from .views.share import blueprint as share_blueprint
    # pylint: enable=import-outside-toplevel

    api.register_blueprint(marketplace_blueprint)
    api.register_blueprint(activities_blueprint)
    api.register_blueprint(myactivities_blueprint)
    api.register_blueprint(application_blueprint)
    api.register_blueprint(banner_blueprint)
    api.register_blueprint(community_blueprint)
    api.register_blueprint(customer_blueprint)
    api.register_blueprint(customer_user_blueprint)
    api.register_blueprint(event_blueprint)
    api.register_blueprint(feedback_blueprint)
    api.register_blueprint(language_blueprint)
    api.register_blueprint(location_blueprint)
    api.register_blueprint(match_blueprint)
    api.register_blueprint(notification_blueprint)
    api.register_blueprint(offer_blueprint)
    api.register_blueprint(proposal_blueprint)
    api.register_blueprint(onboarding_blueprint)
    api.register_blueprint(position_blueprint)
    api.register_blueprint(performer_blueprint)
    api.register_blueprint(post_blueprint)
    api.register_blueprint(post_application_blueprint)
    api.register_blueprint(post_type_blueprint)
    api.register_blueprint(skill_blueprint)
    api.register_blueprint(user_blueprint)
    api.register_blueprint(backgroundpicture_blueprint)
    api.register_blueprint(share_blueprint)

    return app
