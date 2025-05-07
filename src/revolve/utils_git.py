import os
import shutil
import subprocess
from datetime import datetime

import subprocess
import os
from datetime import datetime
import shutil


def run_git_command(args, cwd="."):
    result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git error: {result.stderr.strip()}")
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def init_or_attach_git_repo():
    git_check = os.environ.get("GIT_PUSH_CHANGES", "false").lower() == "true"
    if git_check:
        repo_dir = os.environ.get("GIT_REPO_PATH", "src/revolve/source_generated")
        remote_url = os.environ.get("GIT_REPO_URL", "https://github.com/maheshpec/revolve-generated")
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
        repo_dir = os.environ.get("GIT_REPO_PATH", "src/revolve/source_generated")
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
        repo_dir = os.environ.get("GIT_REPO_PATH", "src/revolve/source_generated")
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


# def _run_git_command(args, cwd):
#     result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
#     if result.returncode != 0:
#         print(f"Git error: {result.stderr.strip()}")
#         print(result.stdout.strip())
#     return result


# def init_git_repo_if_needed(target_dir="src/revolve/source_generated"):
#     if not os.path.exists(target_dir):
#         os.makedirs(target_dir)
        
#     if not os.path.isdir(os.path.join(target_dir, ".git")):
#         print(f"Initializing new git repo in {target_dir}")
#         run_git_command(["init"], cwd=target_dir)
#         run_git_command(["config", "user.name", "AutoCommitBot"], cwd=target_dir)
#         run_git_command(
#             ["config", "user.email", "autocommit@example.com"], cwd=target_dir
#         )


# def commit_changes(
#     target_dir="src/revolve/source_generated",
#     message: str = None,
#     description: str = None,
# ):
#     """
#     Commit any changed .py files in `target_dir`.
#     - `message`: the commit’s subject line.
#     - `description`: optional body text.
#     """
#     init_git_repo_if_needed(target_dir)

#     # Stage all .py files
#     run_git_command(["add", "*.py"], cwd=target_dir)

#     # Nothing to commit?
#     status = run_git_command(["status", "--porcelain"], cwd=target_dir)
#     if not status.stdout.strip():
#         print("No changes to commit.")
#         return

#     # Fallback subject line if none provided
#     if not message:
#         message = f"Auto commit at {datetime.now():%Y-%m-%d %H:%M:%S}"

#     # Build the commit command
#     commit_args = ["commit", "-m", message]
#     if description:
#         commit_args += ["-m", description]

#     # Run it
#     run_git_command(commit_args, cwd=target_dir)
#     print("Committed:", message)
#     if description:
#         print("Description:", description)

# def reset_repo(target_dir="src/revolve/source_generated"):
#     git_path = os.path.join(target_dir, ".git")
#     if os.path.exists(git_path):
#         print(f"Removing existing Git repo in {target_dir}")
#         shutil.rmtree(git_path)
#     else:
#         print("No Git repo to remove.")


# def start_over_repo(
#     target_dir="src/revolve/source_generated", initial_message="Initial commit"
# ):
#     reset_repo(target_dir)
#     init_git_repo_if_needed(target_dir)
#     run_git_command(["add", "*.py"], cwd=target_dir)
#     run_git_command(["commit", "-m", initial_message], cwd=target_dir)
#     print("Repo reset and initial commit created.")


# if __name__ == "__main__":
#     path = "src/revolve/source_generated"
#     init_git_repo_if_needed(path)
#     commit_changes(path, "Initial commit")


if __name__ == "__main__":
    repo_path = "src/revolve/source_generated"
    remote_url = "https://github.com/maheshpec/revolve-generated"

    init_or_attach_git_repo(repo_path, remote_url)
    create_branch_with_timestamp(repo_path)
    commit_and_push_changes(repo_path, "test for creating a new branch and pushing")
