FROM python:3.9.6-slim-buster

WORKDIR /canvara

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /canvara

# TODO: switch to non-root user

COPY pip_requirements.txt pip_requirements.txt
RUN pip install -r pip_requirements.txt

COPY src .
COPY deploy/docker_run.sh .
RUN chmod +x docker_run.sh

EXPOSE 8000

ENTRYPOINT ["sh", "./docker_run.sh"]

