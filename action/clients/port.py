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
    This function uses a CLIENT_ID and CLIENT_SECRET from environment variables
    """

    credentials = {'clientId': CLIENT_ID, 'clientSecret': CLIENT_SECRET}

    response = requests.post(f"{API_URL}/auth/access_token", json=credentials)

    if response.status_code != 200:
        logger.error('Failed to get Port access token')
        logger.error(json.dumps(response.json()))
        raise Exception('Failed to get Port access token')

    return response.json()['accessToken']


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


def create_port_entity(blueprint_identifier: str, body: dict, run_id: str = None):
    token = get_port_api_token()
    headers = construct_headers(token)

    params = construct_params(run_id)

    response = requests.post(f'{API_URL}/blueprints/{blueprint_identifier}/entities', json=body, params=params, headers=headers)

    if response.status_code != 200 and response.status_code != 201:
        logger.error('Failed to create entity')
        logger.error(json.dumps(response.json()))
    else:
        logger.info(f'Created new Port entity: {response.json()["entity"]["identifier"]}')

    return response.status_code


def add_action_log_message(run_id: str, message: str):
    '''
    Adds a new log line to the specified Port self-service action run
    '''
    token = get_port_api_token()

    headers = construct_headers(token)

    body = {
        "message": message
    }

    response = requests.post(f"{API_URL}/actions/runs/{run_id}/logs", json=body, headers=headers)
    if response.status_code != 200 and response.status_code != 201:
        logger.error('Failed to add log line to run ID')
        logger.error(f'Desired message: {message}')
        logger.error(json.dumps(response.json()))
    else:
        logger.debug('Added new log line to action')

    return response.status_code


def report_action_status(run_id: str, status: str, message: str, links: list = None):
    '''
    Reports to Port on the status of an action run
    '''
    token = get_port_api_token()

    headers = construct_headers(token)

    body = {
        "summary": message,
        "link": links
    }

    logger.info(f'Reporting action {run_id} status:')
    logger.info(json.dumps(body))
    response = requests.patch(f'{API_URL}/actions/runs/{run_id}', json=body, headers=headers)
    if response.status_code != 200 and response.status_code != 201:
        logger.error('Failed to update action run')
        logger.error(json.dumps(response.json()))
    else:
        logger.info(response.status_code)

    return response.status_code
