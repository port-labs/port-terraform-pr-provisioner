from github import Github
from consts import GH_ORGANIZATION, GH_ACCESS_TOKEN, GH_REPOSITORY, GH_DEFAULT_BRANCH
import logging
import json
from log_utils import log_and_add_action_log_line

logger = logging.getLogger('terraform-pr-provisioner.github')

g = Github(GH_ACCESS_TOKEN)
repo = g.get_repo(f"{GH_ORGANIZATION}/{GH_REPOSITORY}")


def create_branch(run_id: str, source_branch_name=GH_DEFAULT_BRANCH):
    log_and_add_action_log_line(logger, run_id, message=f"🗒️ Creating new branch for action")
    source_branch = repo.get_branch(source_branch_name)
    repo.create_git_ref(ref=f"refs/heads/{run_id}", sha=source_branch.commit.sha)
    log_and_add_action_log_line(logger, run_id, message=f"✅ Branch created")


def create_file(name: str, message: str, branch_name: str, content: str):
    repo.create_file(name, message, branch=branch_name, content=content)


def get_file_contents(name: str, ref: str):
    return repo.get_contents(name, ref)


def update_file(path, message, content, sha, branch):
    repo.update_file(path, message, content, sha, branch)


def create_pr(title: str, body: str, head_branch: str, base_branch: str = GH_DEFAULT_BRANCH):
    return repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)


def generate_new_resource_pr_description(params):
    return f'''Adding a new DocDB resource to the set of existing resources tracked in our Terraform.
            
DB name: `{params['db_name']}`

Requested DB parameters:
```
{json.dumps(params, indent=4)}
```
'''


def generate_update_resource_pr_description(db_identifier, params):
    return f'''Updating the definition of existing DocDB {db_identifier} in our Terraform
            
DB name: `{db_identifier}`

Updated variables (`null` means the value will not be updated):
```
{json.dumps(params, indent=4)}
```

'''
