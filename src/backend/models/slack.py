import json

import requests
from backend.common.config import get_canvara_config

from backend.common.exceptions import DoesNotExistError


def slack_notification_response(res):
    msg = ""
    is_success = res["ok"]
    if 'error' in res:
        msg = res["error"]
    elif is_success:
        msg = "Notification sent successfully"
    notification_response = {"is_success": is_success, "message": msg}
    print("response: ", res)
    return notification_response


def send_slack_notification(user, text):
    payload = json.dumps({
        "channel": user.slack_id,
        "text": text
    })

    # slack config
    canvara_config = get_canvara_config()
    slack_config = canvara_config['slack']
    # Slack notification url
    url = slack_config['url']
    # Slack token
    token = slack_config['token']

    # Headers
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    }

    # sending post request and saving response as response object
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)

    return response


def validate_slack_details(user):
    if user.slack_id is None:
        raise DoesNotExistError(f"User '{user.username}' does not have any registered slack details")


def check_slack_details(user, slack_id, workspace_id):
    if user.slack_id == slack_id and user.workspace_id == workspace_id:
        return {
            'is_success': True,
            'message': 'Slack details update successfully'
        }
    return {
        'is_success': False,
        'message': 'Unable to update Slack details'
    }
