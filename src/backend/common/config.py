import os

import sqlalchemy.engine.url


def get_canvara_config():
    config = {}
    config['user_uploads'] = {
        's3_bucket': os.environ['S3_USER_UPLOADS_BUCKET']
    }

    sqlalchemy_url = sqlalchemy.engine.url.URL.create(
        'postgresql',
        username=os.environ['POSTGRES_USERNAME'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ['POSTGRES_HOST'],
        port=os.environ['POSTGRES_PORT'],
        database=os.environ['POSTGRES_DATABASE']
    )

    config['database'] = {
        'sqlalchemy.url': sqlalchemy_url.render_as_string(hide_password=False),
        # 'sqlalchemy.echo':'True'
    }

    config['slack'] = {
        'url': os.environ['SLACK_POST_MESSAGE_URL'],
        'token': os.environ['SLACK_CANVARA_APP_BOT_TOKEN']
    }

    config['rchilli'] = {
        'apiurl': os.environ['RCHILLI_API_URL'],
        'userkey': os.environ['RCHILLI_USER_KEY'],
        'subuserid': os.environ['RCHILLI_SUB_USER_ID'],
        'version': '8.0.0'
    }

    return config
