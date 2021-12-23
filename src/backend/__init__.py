import os

from flask import Flask
from flask_cognito import CognitoAuth
from flask_cors import CORS


def register_api(app, view, endpoint, url, methods):
    view_func = view.as_view(endpoint)
    app.add_url_rule(url, view_func=view_func, methods=methods)


def register_position_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.position import (PositionAPI)
    # pylint: enable=import-outside-toplevel

    position_view = PositionAPI.as_view('position_api')
    app.add_url_rule('/positions', view_func=position_view, methods=['GET', 'POST'])
    app.add_url_rule('/positions/<position_id>', view_func=position_view, methods=['GET', 'PUT', 'DELETE'])


def register_community_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.community import (
        CommunityAPI, CommunityLogoAPI, CommunityLogoByIdAPI, CommunityVideoAPI, CommunityVideoByIdAPI,
        CommunityAnnouncementAPI, CommunityMembershipAPI, CommunityMembershipByIdAPI,
        CommunityGalleryAPI, CommunityGalleryByIdAPI
        )
    # pylint: enable=import-outside-toplevel

    community_view = CommunityAPI.as_view('community_api')
    app.add_url_rule('/communities', view_func=community_view, methods=['GET', 'POST'])
    app.add_url_rule('/communities/<community_id>', view_func=community_view, methods=['GET', 'PUT', 'DELETE'])

    register_api(app, CommunityLogoAPI, 'community_logo_api', '/communities/<community_id>/community_logo', ['PUT', ])
    register_api(
        app, CommunityLogoByIdAPI, 'community_logo_by_id_api', '/communities/<community_id>/community_logo/<upload_id>', [
            'PUT', 'DELETE'])

    register_api(app, CommunityVideoAPI, 'community_video_api', '/communities/<community_id>/overview_video', ['PUT', ])
    register_api(
        app, CommunityVideoByIdAPI, 'community_video_by_id_api', '/communities/<community_id>/overview_video/<upload_id>', [
            'PUT', 'DELETE'])

    register_api(
        app, CommunityAnnouncementAPI, 'community_announcement_api', '/communities/<community_id>/announcements', ['POST'])
    register_api(
        app, CommunityAnnouncementAPI, 'community_announcement_by_id_api',
        '/communities/<community_id>/announcements/<announcement_id>', ['PUT', 'DELETE'])

    register_api(app, CommunityMembershipAPI, 'community_member_api', '/communities/<community_id>/members', [
        'POST', 'DELETE'])
    register_api(
        app, CommunityMembershipByIdAPI, 'community_member_by_id_api', '/communities/<community_id>/members/<membership_id>', [
            'PUT'])

    register_api(app, CommunityGalleryAPI, 'community_gallery_api', '/communities/<community_id>/gallery', ['PUT', ])
    register_api(
        app, CommunityGalleryByIdAPI, 'community_gallery_by_id_api', '/communities/<community_id>/gallery/<upload_id>', [
            'PUT', 'DELETE'])


def register_event_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.event import EventAPI, EventLogoAPI, EventLogoByIdAPI, EventVideoAPI, EventVideoByIdAPI
    # pylint: enable=import-outside-toplevel

    event_view = EventAPI.as_view('event_api')
    app.add_url_rule('/events', view_func=event_view, methods=['GET', 'POST'])
    app.add_url_rule('/events/<event_id>', view_func=event_view, methods=['GET', 'PUT', 'DELETE'])

    register_api(app, EventLogoAPI, 'event_logo_api', '/events/<event_id>/event_logo', ['PUT', ])
    register_api(
        app, EventLogoByIdAPI, 'event_logo_by_id_api', '/events/<event_id>/event_logo/<upload_id>', ['PUT', 'DELETE'])

    register_api(app, EventVideoAPI, 'event_video_api', '/events/<event_id>/overview_video', ['PUT', ])
    register_api(app, EventVideoByIdAPI, 'event_video_by_id_api', '/events/<event_id>/overview_video/<upload_id>', [
        'PUT', 'DELETE'])


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
        methods=['PUT', 'DELETE']
    )


def register_customer_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.customer import CustomerAPI
    # pylint: enable=import-outside-toplevel

    customer_view = CustomerAPI.as_view('customer_api')
    app.add_url_rule('/customers', view_func=customer_view, methods=['GET', 'POST'])
    app.add_url_rule('/customers/<customer_id>', view_func=customer_view, methods=['GET', 'PUT', 'DELETE'])


def register_feedback_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.feedback import PerformerFeedbackAPI, PosterFeedbackAPI
    # pylint: enable=import-outside-toplevel

    register_api(
        app,
        PerformerFeedbackAPI,
        'performer_feedback_api',
        '/posts/<post_id>/performers/<performer_id>/feedback',
        ['GET', 'POST']
    )
    register_api(app, PosterFeedbackAPI, 'post_feedback_api', '/posts/<post_id>/feedback', ['GET', 'POST'])


def register_match_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.match import MatchAPI
    # pylint: enable=import-outside-toplevel

    match_view = MatchAPI.as_view('match_api')
    app.add_url_rule('/matches', view_func=match_view, methods=['GET', 'POST'])
    app.add_url_rule('/matches/<match_id>', view_func=match_view, methods=['GET', 'PUT', 'DELETE'])


def register_notification_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.notification import NotificationAPI, NotificationByIdAPI
    # pylint: enable=import-outside-toplevel

    register_api(app, NotificationAPI, 'notification_api', '/notifications', ['GET', ])
    register_api(app, NotificationByIdAPI, 'notification_by_id_api', '/notifications/<notification_id>', ['PUT', 'DELETE'])


def register_onboarding_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.onboarding import (
        CurrentSkillAPI, DesiredSkillAPI, LinkedInAPI, ProductPreferenceAPI, ProfilePictureAPI, ProfilePictureByIdAPI)
    # pylint: enable=import-outside-toplevel

    register_api(app, CurrentSkillAPI, 'current_skill_api', '/onboarding/current_skills', ['POST', ])
    register_api(app, DesiredSkillAPI, 'desired_skill_api', '/onboarding/desired_skills', ['POST', ])
    register_api(app, LinkedInAPI, 'linkedin_api', '/onboarding/linkedin', ['POST', ])
    register_api(app, ProductPreferenceAPI, 'product_preference_api', '/onboarding/product_preferences', ['GET', 'POST'])
    register_api(app, ProfilePictureAPI, 'onboarding_profile_picture_api', '/onboarding/profile_picture', ['PUT', ])
    register_api(
        app,
        ProfilePictureByIdAPI,
        'onboarding_profile_picture_by_id_api',
        '/onboarding/profile_picture/<upload_id>',
        ['PUT', ])


def register_performer_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.performer import PerformerAPI, PerformerByIdAPI
    # pylint: enable=import-outside-toplevel

    register_api(app, PerformerAPI, 'post_performer_api', '/posts/<post_id>/performers', ['GET', ])
    register_api(
        app,
        PerformerByIdAPI,
        'post_performer_by_id_api',
        '/posts/<post_id>/performers/<performer_id>',
        ['GET', 'PUT'])


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
    app.add_url_rule('/posts/<post_id>/video/<upload_id>', view_func=post_video_by_id_view, methods=['PUT', 'DELETE'])

    post_bookmark_view = PostBookmarkAPI.as_view('post_bookmark_api')
    app.add_url_rule('/posts/<post_id>/bookmark', view_func=post_bookmark_view, methods=['PUT', 'DELETE'])

    post_like_view = PostLikeAPI.as_view('post_like_api')
    app.add_url_rule('/posts/<post_id>/like', view_func=post_like_view, methods=['PUT', 'DELETE'])

    register_api(app, LanguageAPI, 'language_api', '/languages', ['GET', ])
    register_api(app, LocationAPI, 'location_api', '/locations', ['GET', ])
    register_api(app, PostTypeAPI, 'post_type_api', '/post_types', ['GET', ])


def register_user_apis(app):
    # pylint: disable=import-outside-toplevel
    from backend.views.user import (
        CustomerUserAPI, FunFactAPI, FunFactByIdAPI, ProfilePictureAPI, ProfilePictureByIdAPI,
        MentorshipVideoAPI, MentorshipVideoByIdAPI, UserAPI)
    # pylint: enable=import-outside-toplevel

    register_api(app, CustomerUserAPI, 'customer_user_api', '/customers/<customer_id>/users', ['GET', 'POST'])

    user_view = UserAPI.as_view('user_api')
    app.add_url_rule('/users/me', view_func=user_view, methods=['GET', ])
    app.add_url_rule('/users/<user_id>', view_func=user_view, methods=['GET', 'PUT'])

    register_api(app, FunFactAPI, 'fun_fact_api', '/users/<user_id>/fun_fact', ['PUT', ])
    register_api(app, FunFactByIdAPI, 'fun_fact_by_id_api', '/users/<user_id>/fun_fact/<upload_id>', ['PUT', 'DELETE'])

    register_api(app, ProfilePictureAPI, 'profile_picture_api', '/users/<user_id>/profile_picture', ['PUT', ])
    register_api(
        app, ProfilePictureByIdAPI, 'profile_picture_by_id_api', '/users/<user_id>/profile_picture/<upload_id>', ['PUT', ])

    register_api(app, MentorshipVideoAPI, 'mentorship_video_api', '/users/<user_id>/mentorship_video', ['PUT', ])
    register_api(app, MentorshipVideoByIdAPI, 'mentorship_video_by_id_api', '/users/<user_id>/mentorship_video/<upload_id>', [
        'PUT', 'DELETE'])


def create_app():  # pylint: disable=too-many-locals
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

    from backend.common.exceptions import APP_ERROR_HANDLERS  # pylint: disable=import-outside-toplevel
    for exception_type, exception_handler in APP_ERROR_HANDLERS.items():
        app.register_error_handler(exception_type, exception_handler)

    from backend.models.db import CanvaraDB  # pylint: disable=import-outside-toplevel
    CanvaraDB.init_db()

    # pylint: disable=import-outside-toplevel
    from backend.views.banner import BannerAPI
    from backend.views.skill import SkillAPI
    # pylint: enable=import-outside-toplevel

    register_position_apis(app)
    register_community_apis(app)
    register_event_apis(app)
    register_application_apis(app)
    register_customer_apis(app)
    register_feedback_apis(app)
    register_onboarding_apis(app)
    register_match_apis(app)
    register_notification_apis(app)
    register_post_apis(app)
    register_performer_apis(app)
    register_user_apis(app)

    register_api(app, SkillAPI, 'skill_api', '/skills', ['GET', ])
    register_api(app, BannerAPI, 'banner_api', '/banners', ['GET', ])

    return app
