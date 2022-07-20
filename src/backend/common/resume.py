import base64
import json
import requests

from backend.common.exceptions import InvalidOperationError


class Resume():  # pylint: disable=too-few-public-methods
    @classmethod
    def convert_resume_to_json_data(cls, file_path, file_name):
        try:
            api_url = "https://rest.rchilli.com/RChilliParser/Rchilli/parseResumeBinary"
            user_key = 'KR0RC54B'
            version = '8.0.0'
            sub_userid = 'Canvara Inc.'

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
        except ValueError as ex:
            raise InvalidOperationError(f"Unable to parse {file_name}") from ex
