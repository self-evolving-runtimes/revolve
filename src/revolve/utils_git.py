import os
import shutil
import subprocess
from datetime import datetime


def run_git_command(args, cwd):
    result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git error: {result.stderr.strip()}")
        print(result.stdout.strip())
    return result


def init_git_repo_if_needed(target_dir="src/revolve/source_generated"):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    if not os.path.isdir(os.path.join(target_dir, ".git")):
        print(f"Initializing new git repo in {target_dir}")
        run_git_command(["init"], cwd=target_dir)
        run_git_command(["config", "user.name", "AutoCommitBot"], cwd=target_dir)
        run_git_command(
            ["config", "user.email", "autocommit@example.com"], cwd=target_dir
        )


def commit_changes(
    target_dir="src/revolve/source_generated",
    message: str = None,
    description: str = None,
):
    """
    Commit any changed .py files in `target_dir`.
    - `message`: the commit’s subject line.
    - `description`: optional body text.
    """
    init_git_repo_if_needed(target_dir)

    # Stage all .py files
    run_git_command(["add", "*.py"], cwd=target_dir)

    # Nothing to commit?
    status = run_git_command(["status", "--porcelain"], cwd=target_dir)
    if not status.stdout.strip():
        print("No changes to commit.")
        return

    # Fallback subject line if none provided
    if not message:
        message = f"Auto commit at {datetime.now():%Y-%m-%d %H:%M:%S}"

    # Build the commit command
    commit_args = ["commit", "-m", message]
    if description:
        commit_args += ["-m", description]

    # Run it
    run_git_command(commit_args, cwd=target_dir)
    print("Committed:", message)
    if description:
        print("Description:", description)

def reset_repo(target_dir="src/revolve/source_generated"):
    git_path = os.path.join(target_dir, ".git")
    if os.path.exists(git_path):
        print(f"Removing existing Git repo in {target_dir}")
        shutil.rmtree(git_path)
    else:
        print("No Git repo to remove.")


def start_over_repo(
    target_dir="src/revolve/source_generated", initial_message="Initial commit"
):
    reset_repo(target_dir)
    init_git_repo_if_needed(target_dir)
    run_git_command(["add", "*.py"], cwd=target_dir)
    run_git_command(["commit", "-m", initial_message], cwd=target_dir)
    print("Repo reset and initial commit created.")


if __name__ == "__main__":
    path = "src/revolve/source_generated"
    init_git_repo_if_needed(path)
    commit_changes(path, "Initial commit")
