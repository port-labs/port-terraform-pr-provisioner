from typing import Literal, Union
from consts import GH_ORGANIZATION, GH_REPOSITORY
from clients.github import create_branch, create_pr, get_file_contents, update_file

import logging

logger = logging.getLogger('terraform-pr-provisioner.provisioner')


def create_doc_db_resource(db_name):
    return '''
resource "aws_docdb_cluster" "port-terraform-provisioner-docdb-{db_name}" {{
cluster_identifier      = "port-terraform-provisioner-docdb-cluster-{db_name}"
engine                  = "docdb"
availability_zones      = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
master_username         = "port"
master_password         = "180%r$RGgb9q"
backup_retention_period = 1
preferred_backup_window = "07:00-09:00"
skip_final_snapshot     = true
}}
'''.format(db_name=db_name)


def create_doc_db_instances_resource(db_name, num_instances):
    return '''
resource "aws_docdb_cluster_instance" "cluster_instances-{db_name}" {{
count              = {num_instances}
identifier         = "docdb-cluster-demo-{db_name}-${{count.index + 1}}"
cluster_identifier = aws_docdb_cluster.port-terraform-provisioner-docdb-{db_name}.id
instance_class     = "db.t3.medium"
}}
'''.format(db_name=db_name, num_instances=num_instances)


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


def create_new_doc_db(params: dict, run_id: str, service_identifier: str) -> Union[Literal['FAILURE'], Literal['SUCCESS']]:
    try:
        print(f'Run ID: {run_id}')
        new_branch_name = run_id
        create_branch(new_branch_name=new_branch_name)
        print('Branch created')
        existing_file = get_file_contents(name=f"main/demo/terraform/main.tf", ref=new_branch_name)
        existing_file_content = existing_file.decoded_content.decode()
        updated_file_content = existing_file_content + create_doc_db_resource(params['db_name']) + create_doc_db_instances_resource(
            params['db_name'], params['num_instances']) + create_port_docdb_entity_resource(params['db_name']) + create_new_cluster_identifier_output_resource(run_id, params['db_name'], service_identifier)
        update_file(existing_file.path, "Added new DB resource to TF file", updated_file_content, existing_file.sha, branch=new_branch_name)
        print('File updated')
        pr = create_pr(
            title=f"Add new DocDB {params['db_name']}",
            body=f'''Adding a new DocDB resource to the set of existing resources tracked in our Terraform.
            
DB name: `{params['db_name']}`

number of instances for new DB: `{params['num_instances']}`''',
            head_branch=new_branch_name)
        print(f"init DocDB creation of DB {params['db_name']} - success, created PR number: {pr.number}")
        return 'SUCCESS', f'https://github.com/{GH_ORGANIZATION}/{GH_REPOSITORY}/pull/{pr.number}'
    except Exception as err:
        logger.error(f"init DocDB creation of DB {params['db_name']} - error: {err}")

    return 'FAILURE', None
