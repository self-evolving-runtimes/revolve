import os
import shutil
import subprocess
from datetime import datetime
from revolve.external import get_source_folder



def run_git_command(args, cwd="."):
    result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git error: {result.stderr.strip()}")
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def init_or_attach_git_repo():
    git_check = os.environ.get("GIT_PUSH_CHANGES", "false").lower() == "true"
    if git_check:
        repo_dir = get_source_folder()
        remote_url = os.environ.get("GIT_REPO_URL", None)
        if not remote_url:
            raise ValueError("GIT_REPO_URL environment variable is not set.")
        user_name = os.environ.get("GIT_USER_NAME", "AutoCommitBot")
        user_email = os.environ.get("GIT_USER_EMAIL", "autocommit@example.com")

        if os.path.exists(repo_dir):
            print(f"Removing existing directory: {repo_dir}")
            shutil.rmtree(repo_dir)

        print(f"Cloning from {remote_url} into {repo_dir}")
        run_git_command(["clone", remote_url, repo_dir])

        run_git_command(["config", "user.name", user_name], cwd=repo_dir)
        run_git_command(["config", "user.email", user_email], cwd=repo_dir)

        print("Git repo cloned and configured.")

def create_branch_with_timestamp(prefix="source-generated"):
    git_check = os.environ.get("GIT_PUSH_CHANGES", "false").lower() == "true"
    if git_check:
        repo_dir = get_source_folder()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        user_suffix = os.getenv("GIT_BRANCH_NAME_USER_SUFFIX")
        if user_suffix:
            prefix = f"{prefix}-{user_suffix}"
        branch_name = f"{prefix}-{timestamp}"
        run_git_command(["checkout", "-b", branch_name], cwd=repo_dir)
        print(f"Switched to new branch: {branch_name}")
        return branch_name
    return ""


def commit_and_push_changes(message: str, description: str = None):
    git_check = os.environ.get("GIT_PUSH_CHANGES", "false").lower() == "true"
    if git_check:    
        repo_dir = get_source_folder()
        run_git_command(["add", "."], cwd=repo_dir)

        status = run_git_command(["status", "--porcelain"], cwd=repo_dir)
        if not status.strip():
            print("No changes to commit.")
            return

        commit_args = ["commit", "-m", message]
        if description:
            commit_args += ["-m", description]

        run_git_command(commit_args, cwd=repo_dir)

        current_branch = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)
        run_git_command(["push", "-u", "origin", current_branch], cwd=repo_dir)
        print(f"Changes committed and pushed to branch: {current_branch}")
