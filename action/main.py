import json
from resource_definitions import RESOURCE_DEFINITIONS
from terraform_pr_provisioner import create_new_doc_db, update_existing_doc_db
import logging
from log_utils import log_stream_handler
from clients.port import create_port_entity, get_port_api_token, report_action_status
from clients.slack import send_approval_message

logging.basicConfig(handlers=[log_stream_handler], level=logging.DEBUG)

logger = logging.getLogger('terraform-pr-provisioner.main')


def lambda_handler(event, context):
    req_body = json.loads(event['body'])
    action_identifier = req_body['payload']['action']['identifier']
    run_id = req_body['context']['runId']
    properties = req_body['payload']['properties']
    entity_properties = req_body['payload']['entity']
    if action_identifier == 'add_document_db':
        service_identifier = entity_properties['identifier']
        input_obj = RESOURCE_DEFINITIONS[action_identifier]
        for k, v in RESOURCE_DEFINITIONS[action_identifier].items():
            input_obj[k] = properties[k]
        # db_name = "morp"
        # num_instances = "1"
        status, pr_url = create_new_doc_db(input_obj, run_id, service_identifier)
        if status == 'FAILURE':
            return {
                "body": {
                    "message": "Encountered error"
                },
                "statusCode": 500
            }
    elif action_identifier == 'update_document_db':
        db_identifier = entity_properties['title']
        input_obj = RESOURCE_DEFINITIONS[action_identifier]
        for k, v in RESOURCE_DEFINITIONS[action_identifier].items():
            input_obj[k] = properties.get(k, None)
        # db_name = "morp"
        # num_instances = "1"
        status, pr_url = update_existing_doc_db(input_obj, run_id, db_identifier)
        if status == 'FAILURE':
            return {
                "body": {
                    "message": "Encountered error"
                },
                "statusCode": 500
            }
    token = get_port_api_token()
    result = report_action_status(token, run_id, 'IN_PROGRESS', f'Created new PR for the requested resource: {pr_url}')

    print(f'Got: {result}')
    send_approval_message(pr_url, action_identifier)

    return {
        "body": {
            "message": "PR created"
        },
        "statusCode": 200
    }


if __name__ == "__main__":
    lambda_handler(None, None)
