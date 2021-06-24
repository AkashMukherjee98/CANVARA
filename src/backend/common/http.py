import http

from flask import Response


def make_no_content_response():
    return Response('', status=http.HTTPStatus.NO_CONTENT, content_type='application/json')
