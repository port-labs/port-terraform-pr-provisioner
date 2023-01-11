import json
from terraform_pr_provisioner import create_new_doc_db
import logging
from log_utils import log_stream_handler
from clients.port import create_port_entity, get_port_api_token, report_action_status
from clients.slack import send_approval_message

logging.basicConfig(handlers=[log_stream_handler], level=logging.DEBUG)

logger = logging.getLogger('terraform-pr-provisioner.main')


def lambda_handler(event, context):
    req_body = json.loads(event['body'])
    properties = req_body['payload']['properties']
    entity_properties = req_body['payload']['entity']
    service_identifier = entity_properties['identifier']
    run_id = req_body['context']['runId']
    db_name = properties['db_name']
    num_instances = properties['num_instances']
    # db_name = "morp"
    # num_instances = "1"
    status, pr_url = create_new_doc_db({"db_name": db_name, "num_instances": num_instances}, run_id, service_identifier)
    # Need to create DB Blueprint
    # Need to create a DB entity and create a relation to the microservice
    # Need to send a slack message when the PR is open to ask for approval (bonus)
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
    send_approval_message(pr_url)

    return {
        "body": {
            "message": "PR created"
        },
        "statusCode": 200
    }


if __name__ == "__main__":
    lambda_handler(None, None)
