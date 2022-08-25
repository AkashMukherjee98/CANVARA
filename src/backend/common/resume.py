import base64
import json
import requests

from backend.common.config import get_canvara_config
from backend.common.exceptions import InvalidOperationError


class Resume():  # pylint: disable=too-few-public-methods
    @classmethod
    def convert_resume_url_to_json_data(cls, file_url):  # pylint: disable=too-many-locals
        try:
            canvara_config = get_canvara_config()
            rchilli_config = canvara_config['rchilli']

            api_url = rchilli_config['apiurl']
            user_key = rchilli_config['userkey']
            sub_userid = rchilli_config['subuserid']
            version = rchilli_config['version']

            headers = {'content-type': 'application/json'}
            body = """{
                "url":\"""" + file_url + """\",
                \"userkey":\"""" + user_key + """\",
                \"version\":\"""" + version + """\",
                \"subuserid\":\"""" + sub_userid + """\"
            }"""

            response = requests.post(api_url, data=body, headers=headers)
            resp = json.loads(response.text)
            return resp["ResumeParserData"]
        except Exception as ex:
            raise InvalidOperationError(f"Unable to parse {file_url}") from ex

    @classmethod
    def convert_resume_file_to_json_data(cls, file_path, file_name):  # pylint: disable=too-many-locals
        try:
            canvara_config = get_canvara_config()
            rchilli_config = canvara_config['rchilli']

            api_url = rchilli_config['apiurl']
            user_key = rchilli_config['userkey']
            sub_userid = rchilli_config['subuserid']
            version = rchilli_config['version']

            with open(file_path, "rb") as filepath:
                encoded_string = base64.b64encode(filepath.read())
            data64 = encoded_string.decode('UTF-8')

            headers = {'content-type': 'application/json'}
            body = """{
                "filedata":\"""" + data64 + """\",
                "filename":\"""" + file_name + """\",
                "userkey":\"""" + user_key + """\",
                \"version\":\"""" + version + """\",
                \"subuserid\":\"""" + sub_userid + """\"
            }"""

            response = requests.post(api_url, data=body, headers=headers)
            resp = json.loads(response.text)
            return resp["ResumeParserData"]
        except Exception as ex:
            raise InvalidOperationError(f"Unable to parse {file_path}") from ex
