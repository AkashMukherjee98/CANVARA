FROM python:3.9.5-buster

WORKDIR /canvara

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /canvara
ENV CANVARA_CONFIGS_DIR /canvara/configs

# TODO: switch to non-root user

COPY pip_requirements.txt pip_requirements.txt
RUN pip install -r pip_requirements.txt
CMD backend/db 
CMD alembic upgrade head

COPY src .
COPY configs configs

EXPOSE 8000

#ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8080", "backend:create_app()"]
ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--capture-output", "--access-logfile", "/canvara/logs/api_access.log", "--error-logfile", "/canvara/logs/api_error.log", "backend:create_app()"]

