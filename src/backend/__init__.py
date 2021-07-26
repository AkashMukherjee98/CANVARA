import os

from flask import Flask
from flask_cognito import CognitoAuth
from flask_cors import CORS


def register_api(app, view, endpoint, url, methods):
    view_func = view.as_view(endpoint)
    app.add_url_rule(url, view_func=view_func, methods=methods)


def register_application_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.application import ApplicationAPI, PostApplicationAPI, ApplicationVideoAPI, ApplicationVideoByIdAPI
    # pylint: enable=import-outside-toplevel

    register_api(app, PostApplicationAPI, 'post_application_api', '/posts/<post_id>/applications', ['GET', 'POST'])

    application_view = ApplicationAPI.as_view('application_api')
    app.add_url_rule('/applications', view_func=application_view, methods=['GET', ])
    app.add_url_rule('/applications/<application_id>', view_func=application_view, methods=['GET', 'PUT', 'DELETE'])

    application_video_view = ApplicationVideoAPI.as_view('application_video_api')
    app.add_url_rule('/applications/<application_id>/video', view_func=application_video_view, methods=['PUT'])

    application_video_by_id_view = ApplicationVideoByIdAPI.as_view('application_video_by_id_api')
    app.add_url_rule(
        '/applications/<application_id>/video/<upload_id>',
        view_func=application_video_by_id_view,
        methods=['PUT']
    )


def register_customer_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.customer import CustomerAPI
    # pylint: enable=import-outside-toplevel

    customer_view = CustomerAPI.as_view('customer_api')
    app.add_url_rule('/customers', view_func=customer_view, methods=['GET', 'POST'])
    app.add_url_rule('/customers/<customer_id>', view_func=customer_view, methods=['GET', 'PUT', 'DELETE'])


def register_match_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.match import MatchAPI
    # pylint: enable=import-outside-toplevel

    match_view = MatchAPI.as_view('match_api')
    app.add_url_rule('/matches', view_func=match_view, methods=['GET', 'POST'])
    app.add_url_rule('/matches/<match_id>', view_func=match_view, methods=['GET', 'PUT', 'DELETE'])


def register_onboarding_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.onboarding import (
        CurrentSkillAPI, DesiredSkillAPI, LinkedInAPI, ProductPreferenceAPI, ProfilePictureAPI, ProfilePictureByIdAPI)
    # pylint: enable=import-outside-toplevel

    register_api(app, CurrentSkillAPI, 'current_skill_api', '/onboarding/current_skills', ['POST', ])
    register_api(app, DesiredSkillAPI, 'desired_skill_api', '/onboarding/desired_skills', ['POST', ])
    register_api(app, LinkedInAPI, 'linkedin_api', '/onboarding/linkedin', ['POST', ])
    register_api(app, ProductPreferenceAPI, 'product_preference_api', '/onboarding/product_preferences', ['GET', 'POST'])
    register_api(app, ProfilePictureAPI, 'profile_picture_api', '/onboarding/profile_picture', ['PUT', ])
    register_api(app, ProfilePictureByIdAPI, 'profile_picture_by_id_api', '/onboarding/profile_picture/<upload_id>', ['PUT', ])


def register_post_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.post import (
        LanguageAPI, LocationAPI, PostAPI, PostBookmarkAPI, PostLikeAPI, PostTypeAPI, PostVideoAPI, PostVideoByIdAPI)
    # pylint: enable=import-outside-toplevel

    post_view = PostAPI.as_view('post_api')
    app.add_url_rule('/posts', view_func=post_view, methods=['GET', 'POST'])
    app.add_url_rule('/posts/<post_id>', view_func=post_view, methods=['GET', 'PUT', 'DELETE'])

    post_video_view = PostVideoAPI.as_view('post_video_api')
    app.add_url_rule('/posts/<post_id>/video', view_func=post_video_view, methods=['PUT'])

    post_video_by_id_view = PostVideoByIdAPI.as_view('post_video_by_id_api')
    app.add_url_rule('/posts/<post_id>/video/<upload_id>', view_func=post_video_by_id_view, methods=['PUT'])

    post_bookmark_view = PostBookmarkAPI.as_view('post_bookmark_api')
    app.add_url_rule('/posts/<post_id>/bookmark', view_func=post_bookmark_view, methods=['PUT', 'DELETE'])

    post_like_view = PostLikeAPI.as_view('post_like_api')
    app.add_url_rule('/posts/<post_id>/like', view_func=post_like_view, methods=['PUT', 'DELETE'])

    register_api(app, LanguageAPI, 'language_api', '/languages', ['GET', ])
    register_api(app, LocationAPI, 'location_api', '/locations', ['GET', ])
    register_api(app, PostTypeAPI, 'post_type_api', '/post_types', ['GET', ])


def register_user_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.user import CustomerUserAPI, UserAPI
    # pylint: enable=import-outside-toplevel

    register_api(app, CustomerUserAPI, 'customer_user_api', '/customers/<customer_id>/users', ['GET', 'POST'])

    user_view = UserAPI.as_view('user_api')
    app.add_url_rule('/users/me', view_func=user_view, methods=['GET', ])
    app.add_url_rule('/users/<user_id>', view_func=user_view, methods=['GET', 'PUT'])


def create_app():  # pylint: disable=too-many-locals
    import backend.common.logging  # pylint: disable=import-outside-toplevel
    backend.common.logging.initialize_flask_logging()

    app = Flask(__name__)

    # If we're running under gunicorn, and configure logging to use gunicorn's logger
    if os.environ.get('SERVER_SOFTWARE', '').startswith('gunicorn/'):
        backend.common.logging.initialize_gunicorn_logging(app)

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

    # pylint: disable=import-outside-toplevel
    from backend.views.banner import BannerAPI
    from backend.views.skill import SkillAPI
    # pylint: enable=import-outside-toplevel

    register_application_apis(app)
    register_customer_apis(app)
    register_onboarding_apis(app)
    register_match_apis(app)
    register_post_apis(app)
    register_user_apis(app)

    register_api(app, SkillAPI, 'skill_api', '/skills', ['GET', ])
    register_api(app, BannerAPI, 'banner_api', '/banners', ['GET', ])

    return app
