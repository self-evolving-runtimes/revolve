import os
import shutil
import subprocess
from datetime import datetime


def run_git_command(args, cwd):
    result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git error: {result.stderr.strip()}")
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
    message=None,
):
    init_git_repo_if_needed(target_dir)
    run_git_command(["add", "*.py"], cwd=target_dir)

    # Check if there is anything to commit
    status = run_git_command(["status", "--porcelain"], cwd=target_dir)
    if not status.stdout.strip():
        print("No changes to commit.")
        return

    if not message:
        message = f"Auto commit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    run_git_command(["commit", "-m", message], cwd=target_dir)
    print("Committed:", message)


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
