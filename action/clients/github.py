from github import Github
from consts import GH_ORGANIZATION, GH_ACCESS_TOKEN, GH_REPOSITORY, GH_DEFAULT_BRANCH
import logging

logger = logging.getLogger('terraform-pr-provisioner.github')

g = Github(GH_ACCESS_TOKEN)
repo = g.get_repo(f"{GH_ORGANIZATION}/{GH_REPOSITORY}")


def create_branch(new_branch_name: str, source_branch_name=GH_DEFAULT_BRANCH):
    print('Creating new branch')
    source_branch = repo.get_branch(source_branch_name)
    repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=source_branch.commit.sha)
    print('Branch created')


def create_file(name: str, message: str, branch_name: str, content: str):
    repo.create_file(name, message, branch=branch_name, content=content)


def get_file_contents(name: str, ref: str):
    return repo.get_contents(name, ref)


def update_file(path, message, content, sha, branch):
    repo.update_file(path, message, content, sha, branch)


def create_pr(title: str, body: str, head_branch: str, base_branch: str = GH_DEFAULT_BRANCH):
    return repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)
