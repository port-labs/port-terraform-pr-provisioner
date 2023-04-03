import json
from typing import Literal, Union
from clients.port import add_action_log_message
from resource_definitions import VARIABLE_RESOURCES
from consts import GH_ORGANIZATION, GH_REPOSITORY
from clients.github import create_branch, create_pr, get_file_contents, update_file, generate_new_resource_pr_description, generate_update_resource_pr_description
from log_utils import log_and_add_action_log_line

import logging

logger = logging.getLogger('terraform-pr-provisioner.provisioner')


def create_doc_db_resource(db_name):
    resource_name = f"port-terraform-provisioner-docdb-{db_name}"
    return '''
resource "aws_docdb_cluster" "{resource_name}" {{
cluster_identifier      = "port-terraform-provisioner-docdb-cluster-{db_name}"
engine                  = "docdb"
availability_zones      = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
master_username         = "port"
master_password         = "180%r$RGgb9q"
backup_retention_period = var.{resource_name}_backup_retention_period
preferred_backup_window = "07:00-09:00"
skip_final_snapshot     = var.{resource_name}_skip_final_snapshot
}}
'''.format(resource_name=resource_name, db_name=db_name)


def create_doc_db_instances_resource(db_name):
    resource_name = f"cluster_instances-{db_name}"
    return '''
resource "aws_docdb_cluster_instance" "{resource_name}" {{
count              = var.{resource_name}_count
identifier         = "docdb-cluster-demo-{db_name}-${{count.index + 1}}"
cluster_identifier = aws_docdb_cluster.port-terraform-provisioner-docdb-{db_name}.id
instance_class     = var.{resource_name}_instance_class
}}
'''.format(resource_name=resource_name, db_name=db_name)


def create_port_docdb_entity_resource(db_name):
    return '''
resource "port-labs_entity" "port-terraform-provisioner-docdb-{db_name}" {{
  title      = "{db_name}"
  blueprint  = "database"
  identifier = "{db_name}"
  properties {{
    name  = "type"
    value = "DocumentDB"
  }}
}}
'''.format(db_name=db_name)


def create_new_cluster_identifier_output_resource(run_id, db_name, service_identifier):
    return '''
output "{run_id}" {{
  value = "{db_name}"
}}

output "{run_id}-service_identifier" {{
  value = "{service_identifier}"
}}
'''.format(run_id=run_id, db_name=db_name, service_identifier=service_identifier)


def add_resources_to_existing_vars_defaults_file(existing_vars_defaults_json: dict, params):
    for resource, value in VARIABLE_RESOURCES.items():
        tf_resource_name = f'{resource}-{params["db_name"]}'
        for resource_variable in value:
            dict_update = {
                f'{tf_resource_name}_{resource_variable}': {
                    "default": params[resource_variable]
                }
            }
            existing_vars_defaults_json['variable'].update(dict_update)
    return existing_vars_defaults_json


def add_resources_to_existing_vars_file(existing_vars_json, params):
    logger.info('add_resources_to_existing_vars_file')
    logger.info(VARIABLE_RESOURCES.items())
    logger.info(params.items())
    for resource, var_list in VARIABLE_RESOURCES.items():
        resource_name = f'{resource}-{params["db_name"]}'
        for var in var_list:
            logger.debug("var:", var)
            logger.debug("res_name:", resource_name)
            existing_vars_json[f'{resource_name}_{var}'] = params[var]
    return existing_vars_json


def update_resources_in_existing_vars_file(existing_vars_file_content_json, db_identifier, params):
    for resource_name in [f'port-terraform-provisioner-docdb-{db_identifier}', f'cluster_instances-{db_identifier}']:
        print(resource_name)
        for k, v in params.items():
            print(f'{resource_name}_{k}')
            if f'{resource_name}_{k}' in existing_vars_file_content_json and v:
                existing_vars_file_content_json[f'{resource_name}_{k}'] = v
    return existing_vars_file_content_json


def update_vars_defaults_file_with_new_resource(run_id: str, params):
    target_filename = "main/demo/terraform/variables.tf.json"
    log_and_add_action_log_line(logger, run_id, message=f"🔧 Adding resource defaults for new TF resource to the {target_filename} file")
    log_and_add_action_log_line(logger, run_id, message=f"specified defaults: {str(params.items())}")
    vars_defaults_file = get_file_contents(name=target_filename, ref=run_id)
    vars_defaults_file_content = vars_defaults_file.decoded_content.decode()
    updated_vars_defaults_file_content = json.dumps(
        add_resources_to_existing_vars_defaults_file(json.loads(vars_defaults_file_content), params), indent=4)
    update_file(vars_defaults_file.path, "Added new resource variables defaults to the defaults file",
                updated_vars_defaults_file_content, vars_defaults_file.sha, branch=run_id)
    log_and_add_action_log_line(logger, run_id, message=f"✅ Added resource defaults to the {target_filename} file")


def update_definitions_file_with_new_resource(run_id: str, service_identifier: str, params):
    target_filename = "main/demo/terraform/main.tf"
    log_and_add_action_log_line(logger, run_id, message=f"🔧 Adding resource definitions for new TF resource to the {target_filename} file")
    log_and_add_action_log_line(logger, run_id, message=f"specified parameters: {str(params.items())}")
    existing_tf_definition_file = get_file_contents(name=target_filename, ref=run_id)
    existing_tf_definition_file_content = existing_tf_definition_file.decoded_content.decode()
    updated_tf_definition_file_content = existing_tf_definition_file_content + create_doc_db_resource(params['db_name']) + create_doc_db_instances_resource(
        params['db_name']) + create_port_docdb_entity_resource(params['db_name']) + create_new_cluster_identifier_output_resource(run_id,
                                                                                                                                  params['db_name'],
                                                                                                                                  service_identifier)
    update_file(existing_tf_definition_file.path, "Added new resource definitions to TF file",
                updated_tf_definition_file_content, existing_tf_definition_file.sha, branch=run_id)
    log_and_add_action_log_line(logger, run_id, message=f"✅ Added resource definitions to the {target_filename} file")


def update_vars_file_with_new_resource(run_id: str, params):
    target_filename = "main/demo/terraform/vars.tfvars.json"
    log_and_add_action_log_line(logger, run_id, message=f"🔧 Adding resource variables for new TF resource to the {target_filename} file")
    log_and_add_action_log_line(logger, run_id, message=f"specified parameters: {str(params.items())}")
    vars_file = get_file_contents(name=target_filename, ref=run_id)
    vars_file_content = vars_file.decoded_content.decode()
    updated_vars_file_content = json.dumps(add_resources_to_existing_vars_file(json.loads(vars_file_content), params), indent=4)
    update_file(vars_file.path, "Added new resource variables to tfvars file",
                updated_vars_file_content, vars_file.sha, branch=run_id)
    log_and_add_action_log_line(logger, run_id, message=f"✅ Added resource variables to the {target_filename} file")


def update_vars_file_with_new_values_for_existing_resource(run_id: str, db_identifier: str, params):
    target_filename = "main/demo/terraform/vars.tfvars.json"
    log_and_add_action_log_line(logger, run_id, message=f"🔧 Updating resource variables for existing TF resource in the {target_filename} file")
    log_and_add_action_log_line(logger, run_id, message=f"specified parameters: {str(params.items())}")
    existing_vars_file = get_file_contents(name=target_filename, ref=run_id)
    existing_vars_file_content = existing_vars_file.decoded_content.decode()
    existing_vars_file_content_json = json.loads(existing_vars_file_content)
    updated_existing_vars_file_content = json.dumps(update_resources_in_existing_vars_file(
        existing_vars_file_content_json, db_identifier, params), indent=4)
    update_file(existing_vars_file.path, "Updated existing DB resource definition",
                updated_existing_vars_file_content, existing_vars_file.sha, branch=run_id)
    log_and_add_action_log_line(logger, run_id, message=f"✅ Added resource variables to the {target_filename} file")


def create_new_doc_db(params: dict, run_id: str, service_identifier: str) -> Union[Literal['FAILURE'], Literal['SUCCESS']]:
    """
    Opens a new PR with the following file changes:
    Adds the default values for the newly added TF resources (main/demo/terraform/variables.tf.json)
    Adds the new resource definition for the new resource (main/demo/terraform/main.tf)
    Adds the new variable values for the new resource (main/demo/terraform/vars.tfvars.json)
    """
    try:
        create_branch(run_id=run_id)
        update_vars_defaults_file_with_new_resource(run_id, params)
        update_vars_file_with_new_resource(run_id, params)
        update_definitions_file_with_new_resource(run_id, service_identifier, params)

        log_and_add_action_log_line(logger, run_id, message=f"✅ All files updated")
        log_and_add_action_log_line(logger, run_id, message=f"🔧 Creating new PR")
        pr = create_pr(
            title=f"Add new DocDB {params['db_name']} resource",
            body=generate_new_resource_pr_description(params),
            head_branch=run_id)
        pr_url = f'https://github.com/{GH_ORGANIZATION}/{GH_REPOSITORY}/pull/{pr.number}'
        log_and_add_action_log_line(logger, run_id, message=f"✅ PR created")
        log_and_add_action_log_line(logger, run_id, message=f"Number: {pr.number}")
        log_and_add_action_log_line(logger, run_id, message=f"🔗 PR URL: {pr_url}")
        return 'SUCCESS', pr_url
    except Exception as err:
        logger.error(f"❌ Error adding new DocDB resource: {err}")
        add_action_log_message(run_id, f"❌ Error adding new DoCDB resource: {err}")

    return 'FAILURE', None


def update_existing_doc_db(params: dict, run_id: str, db_identifier: str) -> Union[Literal['FAILURE'], Literal['SUCCESS']]:
    try:
        print(f'Run ID: {run_id}')
        create_branch(run_id=run_id)
        update_vars_file_with_new_values_for_existing_resource(run_id, db_identifier, params)
        # log_and_add_action_log_line(run_id, f"🔧 Updating existing resource definition values in ")
        # existing_vars_file = get_file_contents(name=f"main/demo/terraform/vars.tfvars.json", ref=run_id)
        # existing_vars_file_content = existing_vars_file.decoded_content.decode()
        # existing_vars_file_content_json = json.loads(existing_vars_file_content)
        # updated_existing_vars_file_content = json.dumps(update_resources_in_existing_vars_file(
        #     existing_vars_file_content_json, db_identifier, params), indent=4)
        # update_file(existing_vars_file.path, "Updated existing DB resource definition",
        #             updated_existing_vars_file_content, existing_vars_file.sha, branch=run_id)
        log_and_add_action_log_line(logger, run_id, message=f"✅ All files updated")
        pr = create_pr(
            title=f"Update existing DocDB {db_identifier}",
            body=generate_update_resource_pr_description(db_identifier, params),
            head_branch=run_id)
        pr_url = f'https://github.com/{GH_ORGANIZATION}/{GH_REPOSITORY}/pull/{pr.number}'
        log_and_add_action_log_line(logger, run_id, message=f"✅ PR created")
        log_and_add_action_log_line(logger, run_id, message=f"Number: {pr.number}")
        log_and_add_action_log_line(logger, run_id, message=f"🔗 PR URL: {pr_url}")
        return 'SUCCESS', pr_url
    except Exception as err:
        logger.error(f"❌ Error editing DocDB resource: {err}")
        add_action_log_message(run_id, f"❌ Error editing new DoCDB resource: {err}")

    return 'FAILURE', None
