alembic -c /canvara/backend/db/alembic.ini upgrade head
gunicorn --bind 0.0.0.0:8000 --workers 2 --capture-output --access-logfile /canvara/logs/api_access.log --error-logfile /canvara/logs/api_error.log 'backend:create_app()'
