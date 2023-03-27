import json
from typing import Literal, Union
from resource_definitions import VARIABLE_RESOURCES
from consts import GH_ORGANIZATION, GH_REPOSITORY
from clients.github import create_branch, create_pr, get_file_contents, update_file

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
  identifier = aws_docdb_cluster.port-terraform-provisioner-docdb-{db_name}.cluster_identifier
  properties {{
    name  = "type"
    value = "DocumentDB"
  }}
}}
'''.format(db_name=db_name)


def create_new_cluster_identifier_output_resource(run_id, db_name, service_identifier):
    return '''
output "{run_id}" {{
  value = aws_docdb_cluster.port-terraform-provisioner-docdb-{db_name}.cluster_identifier
}}

output "{run_id}-service_identifier" {{
  value = "{service_identifier}"
}}
'''.format(run_id=run_id, db_name=db_name, service_identifier=service_identifier)


def add_resources_to_existing_vars_defaults_file(existing_vars_defaults_json: dict, params):
    print('add_resources_to_existing_vars_defaults_file')
    print(VARIABLE_RESOURCES.items())
    print(params.items())
    for res, v in VARIABLE_RESOURCES.items():
        res_name = f'{res}-{params["db_name"]}'
        for var in v:
            dict_update = {
                f'{res_name}_{var}': {
                    "default": params[var]
                }
            }
            existing_vars_defaults_json['variable'].update(dict_update)
    return existing_vars_defaults_json


def add_resources_to_existing_vars_file(existing_vars_json, params):
    print('add_resources_to_existing_vars_file')
    print(VARIABLE_RESOURCES.items())
    print(params.items())
    for res, v in VARIABLE_RESOURCES.items():
        res_name = f'{res}-{params["db_name"]}'
        for var in v:
            print("var:", var)
            print("res_name:", res_name)
            existing_vars_json[f'{res_name}_{var}'] = params[var]
    return existing_vars_json


def update_resources_in_existing_vars_file(existing_vars_file_content_json, db_identifier, params):
    for res in [f'port-terraform-provisioner-docdb-{db_identifier}', f'cluster_instances-{db_identifier}']:
        print(res)
        for k, v in params.items():
            print(f'{res}_{k}')
            if f'{res}_{k}' in existing_vars_file_content_json and v:
                existing_vars_file_content_json[f'{res}_{k}'] = v
    return existing_vars_file_content_json


def create_new_doc_db(params: dict, run_id: str, service_identifier: str) -> Union[Literal['FAILURE'], Literal['SUCCESS']]:
    try:
        print(f'Run ID: {run_id}')
        new_branch_name = run_id
        create_branch(new_branch_name=new_branch_name)
        existing_vars_defaults_file = get_file_contents(name=f"main/demo/terraform/variables.tf.json", ref=new_branch_name)
        existing_vars_defaults_file_content = existing_vars_defaults_file.decoded_content.decode()
        updated_existing_vars_defaults_file_content = json.dumps(
            add_resources_to_existing_vars_defaults_file(json.loads(existing_vars_defaults_file_content), params), indent=4)
        existing_vars_file = get_file_contents(name=f"main/demo/terraform/vars.tfvars.json", ref=new_branch_name)
        existing_vars_file_content = existing_vars_file.decoded_content.decode()
        updated_existing_vars_file_content = json.dumps(add_resources_to_existing_vars_file(json.loads(existing_vars_file_content), params), indent=4)
        existing_tf_definition_file = get_file_contents(name=f"main/demo/terraform/main.tf", ref=new_branch_name)
        existing_tf_definition_file_content = existing_tf_definition_file.decoded_content.decode()
        updated_tf_definition_file_content = existing_tf_definition_file_content + create_doc_db_resource(params['db_name']) + create_doc_db_instances_resource(
            params['db_name']) + create_port_docdb_entity_resource(params['db_name']) + create_new_cluster_identifier_output_resource(run_id,
                                                                                                                                      params['db_name'],
                                                                                                                                      service_identifier)
        update_file(existing_tf_definition_file.path, "Added new DB resource to TF file",
                    updated_tf_definition_file_content, existing_tf_definition_file.sha, branch=new_branch_name)
        update_file(existing_vars_file.path, "Added new DB variables to tfvars file",
                    updated_existing_vars_file_content, existing_vars_file.sha, branch=new_branch_name)
        update_file(existing_vars_defaults_file.path, "Added new DB variables to variable defaults file",
                    updated_existing_vars_defaults_file_content, existing_vars_defaults_file.sha, branch=new_branch_name)

        print('File updated')
        pr = create_pr(
            title=f"Add new DocDB {params['db_name']}",
            body=f'''Adding a new DocDB resource to the set of existing resources tracked in our Terraform.
            
DB name: `{params['db_name']}`

Requested DB parameters:
```
{json.dumps(params, indent=4)}
```
''',
            head_branch=new_branch_name)
        print(f"init DocDB creation of DB {params['db_name']} - success, created PR number: {pr.number}")
        return 'SUCCESS', f'https://github.com/{GH_ORGANIZATION}/{GH_REPOSITORY}/pull/{pr.number}'
    except Exception as err:
        logger.error(f"init DocDB creation of DB {params['db_name']} - error: {err}")

    return 'FAILURE', None


def update_existing_doc_db(params: dict, run_id: str, db_identifier: str) -> Union[Literal['FAILURE'], Literal['SUCCESS']]:
    try:
        print(f'Run ID: {run_id}')
        new_branch_name = run_id
        create_branch(new_branch_name=new_branch_name)
        existing_vars_file = get_file_contents(name=f"main/demo/terraform/vars.tfvars.json", ref=new_branch_name)
        existing_vars_file_content = existing_vars_file.decoded_content.decode()
        existing_vars_file_content_json = json.loads(existing_vars_file_content)
        updated_existing_vars_file_content = json.dumps(update_resources_in_existing_vars_file(
            existing_vars_file_content_json, db_identifier, params), indent=4)
        update_file(existing_vars_file.path, "Updated existing DB resource definition",
                    updated_existing_vars_file_content, existing_vars_file.sha, branch=new_branch_name)
        print('File updated')
        pr = create_pr(
            title=f"Update existing DocDB {db_identifier}",
            body=f'''Updating the definition of existing DocDB {db_identifier} in our Terraform
            
DB name: `{db_identifier}`

Updated variables (`null` means the value will not be updated):
```
{json.dumps(params, indent=4)}
```

''',
            head_branch=new_branch_name)
        print(f"init DocDB update of DB {db_identifier} - success, created PR number: {pr.number}")
        return 'SUCCESS', f'https://github.com/{GH_ORGANIZATION}/{GH_REPOSITORY}/pull/{pr.number}'
    except Exception as err:
        logger.error(f"init DocDB update of DB {db_identifier} - error: {err}")

    return 'FAILURE', None
