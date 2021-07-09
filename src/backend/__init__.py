from flask import Flask
from flask_cognito import CognitoAuth, cognito_auth_required
from flask_cors import CORS


def register_api(app, view, endpoint, url, methods):
    view_func = cognito_auth_required(view.as_view(endpoint))
    app.add_url_rule(url, view_func=view_func, methods=methods)


def create_app():  # pylint: disable=too-many-locals
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

    # pylint: disable=import-outside-toplevel
    from backend.views.application import ApplicationAPI, PostApplicationAPI
    from backend.views.customer import CustomerAPI
    from backend.views.match import MatchAPI
    from backend.views.onboarding import CurrentSkillAPI, DesiredSkillAPI, LinkedInAPI, ProductPreferenceAPI
    from backend.views.post import LanguageAPI, LocationAPI, PostAPI, PostTypeAPI, PostVideoAPI, PostVideoByIdAPI
    from backend.views.skill import SkillAPI
    from backend.views.user import CustomerUserAPI, UserAPI
    # pylint: enable=import-outside-toplevel

    customer_view = cognito_auth_required(CustomerAPI.as_view('customer_api'))
    app.add_url_rule('/customers', view_func=customer_view, methods=['GET', 'POST'])
    app.add_url_rule('/customers/<customer_id>', view_func=customer_view, methods=['GET', 'PUT', 'DELETE'])

    match_view = cognito_auth_required(MatchAPI.as_view('match_api'))
    app.add_url_rule('/matches', view_func=match_view, methods=['GET', 'POST'])
    app.add_url_rule('/matches/<match_id>', view_func=match_view, methods=['GET', 'PUT', 'DELETE'])

    register_api(app, CurrentSkillAPI, 'current_skill_api', '/onboarding/current_skills', ['POST', ])
    register_api(app, DesiredSkillAPI, 'desired_skill_api', '/onboarding/desired_skills', ['POST', ])
    register_api(app, LinkedInAPI, 'linkedin_api', '/onboarding/linkedin', ['POST', ])
    register_api(app, ProductPreferenceAPI, 'product_preference_api', '/onboarding/product_preferences', ['GET', 'POST'])
    register_api(app, SkillAPI, 'skill_api', '/skills', ['GET', ])

    post_view = cognito_auth_required(PostAPI.as_view('post_api'))
    app.add_url_rule('/posts', view_func=post_view, methods=['GET', 'POST'])
    app.add_url_rule('/posts/<post_id>', view_func=post_view, methods=['GET', 'PUT', 'DELETE'])

    post_video_view = cognito_auth_required(PostVideoAPI.as_view('post_video_api'))
    app.add_url_rule('/posts/<post_id>/video', view_func=post_video_view, methods=['PUT'])

    post_video_by_id_view = cognito_auth_required(PostVideoByIdAPI.as_view('post_video_by_id_api'))
    app.add_url_rule('/posts/<post_id>/video/<upload_id>', view_func=post_video_by_id_view, methods=['PUT'])

    register_api(app, LanguageAPI, 'language_api', '/languages', ['GET', ])
    register_api(app, LocationAPI, 'location_api', '/locations', ['GET', ])
    register_api(app, PostTypeAPI, 'post_type_api', '/post_types', ['GET', ])

    register_api(app, PostApplicationAPI, 'post_application_api', '/posts/<post_id>/applications', ['GET', 'POST'])

    application_view = cognito_auth_required(ApplicationAPI.as_view('application_api'))
    app.add_url_rule('/applications', view_func=application_view, methods=['GET', ])
    app.add_url_rule('/applications/<application_id>', view_func=application_view, methods=['GET', 'PUT', 'DELETE'])

    register_api(app, CustomerUserAPI, 'customer_user_api', '/customers/<customer_id>/users', ['GET', 'POST'])

    user_view = cognito_auth_required(UserAPI.as_view('user_api'))
    app.add_url_rule('/users/me', view_func=user_view, methods=['GET', ])
    app.add_url_rule('/users/<user_id>', view_func=user_view, methods=['GET', 'PUT'])

    return app
