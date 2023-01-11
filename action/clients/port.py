import json
import os
import requests
import logging

from consts import API_URL

logger = logging.getLogger('terraform-pr-provisioner.port')

CLIENT_ID = os.environ['PORT_CLIENT_ID']
CLIENT_SECRET = os.environ['PORT_CLIENT_SECRET']


def get_port_api_token():
    """
    Get a Port API access token
    This function uses CLIENT_ID and CLIENT_SECRET from config
    """

    credentials = {'clientId': CLIENT_ID, 'clientSecret': CLIENT_SECRET}

    token_response = requests.post(f"{API_URL}/auth/access_token", json=credentials)

    return token_response.json()['accessToken']


def construct_headers(access_token):
    return {
        'Authorization': f'Bearer {access_token}'
    }


def construct_params(run_id: str):
    return {
        "upsert": "true",
        "merge": "true",
        "run_id": run_id
    }


def create_port_entity(access_token: str, blueprint_identifier: str, body: dict, run_id: str = None):
    headers = construct_headers(access_token)

    params = construct_params(run_id)

    response = requests.post(f'{API_URL}/blueprints/{blueprint_identifier}/entities', json=body, params=params, headers=headers)

    if response.status_code != 200 and response.status_code != 201:
        logger.error('Failed to create entity')
        logger.error(json.dumps(response.json()))
    else:
        logger.info(response.status_code)

    return response.status_code


def report_action_status(token: str, run_id: str, status: str, message: str):
    '''
    Reports to Port on the status of an action run ``entity_props``
    '''
    logger.info('Fetching token')

    headers = {
        'Authorization': f'Bearer {token}'
    }

    body = {
        "message": {
            "message": message
        }
    }

    print(f'Reporting action {run_id} status:')
    print(json.dumps(body))
    response = requests.patch(f'{API_URL}/actions/runs/{run_id}', json=body, headers=headers)
    if response.status_code != 200 and response.status_code != 201:
        logger.error('Failed to update action run')
        logger.error(json.dumps(response.json()))
    else:
        logger.info(response.status_code)

    return response.status_code
