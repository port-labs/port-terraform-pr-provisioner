import requests
import json
from consts import SLACK_WEBHOOK_URL


def send_approval_message(pr_url, action_identifier):
    if action_identifier == 'add_document_db':
        messageText = "A new DocDB *provision* request is awaiting your approval"
    elif action_identifier == 'update_document_db':
        messageText = "A new DocDB definition *update* request is awaiting your approval"
    message = {
        "text": messageText,
        "username": 'Port Reporter',
        "icon_emoji": ':port:',
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": messageText
                },
                "accessory": {
                    "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View request",
                                "emoji": True
                            },
                    "value": "approval_pr_url",
                    "url": pr_url,
                    "action_id": "button-action"
                }
            }
        ]
    }

    response = requests.post(SLACK_WEBHOOK_URL, json=message)
    print(f'slack response: {response.status_code}')
