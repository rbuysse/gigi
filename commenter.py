#!/usr/bin/env python3
import os
import subprocess
import sys

docs_url = "https://clouddocs.healthpartners.com/foo/bar/baz/"
teams_url = "https://teams.microsoft.com/l/channel/19%3a7b1b1b7b7b1e4b1b9b1b1b1b1b1b1b1%40thread.tacv2/Cloud%2520Engineering%2520Teams?groupId="

def check_yaml_added(file_path):
    command = f'gh pr diff {pr_number}'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        patch = result.stdout
        file_diff = extract_file_diff(patch, file_path)
        if file_diff:
            added_lines = []
            for line in file_diff.splitlines():
                # Check if the line starts with '+' and is not part of the file header
                if line.startswith('+') and not line.startswith('+++'):
                    added_lines.append(line)
            yaml_added = "automated:\n" in "\n".join(added_lines)
            return yaml_added
        else:
            print(f"No diff found for file: {file_path}")
            return False
    else:
        print(f"Failed to get file patch: {result.stderr}")
        return False

def extract_file_diff(patch, file_path):
    file_diff = []
    in_file_diff = False
    for line in patch.splitlines():
        if line.startswith(f"diff --git a/{file_path} b/{file_path}"):
            in_file_diff = True
        elif line.startswith("diff --git") and in_file_diff:
            break
        if in_file_diff:
            file_diff.append(line)
    return "\n".join(file_diff)

def post_comment(message):
    command = f'gh pr comment {pr_number} --body "{message}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"I left a comment on PR: {pr_number}!")
    else:
        print(f"Failed to post comment: {result.stderr}")

def get_changed_files(pr_number=None):
    pr_number = os.getenv('GITHUB_PR_NUMBER')

    command = f'gh pr view {pr_number} --json files --jq ".files[].path"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        changed_files = result.stdout.splitlines()
        return changed_files
    else:
        print(f"Failed to get changed files: {result.stderr}")
        return []

def main(pr_number):
    auto_sync_appsets=[]
    auto_sync_enabled=False
    target_directory = 'applicationsets'
    changed_files = get_changed_files()
    for file_path in changed_files:
        if target_directory in file_path:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                if check_yaml_added(file_path):
                    print(f"This PR enables autosync for {file_path}!")
                    message = f"Your changes to {file_path} included enabling autosync!"
                    auto_sync_enabled=True
                    auto_sync_appsets.append(file_path)

    if auto_sync_enabled==True:
        formatted_appsets = "\n    ".join(auto_sync_appsets)
        message = (
            f"""**WARNING:** This PR enables Argo autosync for one or more applications.
Once merged, Argo will attempt to apply the charts in the monorepo to the
clusters every three minutes.

**This may break your application!**

Please familiarize yourself with the [guidance from the Cloud Team]({docs_url}) and
if you have any questions please reach out in the [Cloud Engineering Teams channel]({teams_url}).

Have a nice day!

The following applicationsets will be autosynced:

    {formatted_appsets}
    """
        )
        post_comment(message)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        pr_number = sys.argv[1]
    else:
        pr_number = os.getenv('PR_NUMBER')
        if not pr_number:
            print("Usage: commenter.py <pr_number> or set PR_NUMBER environment variable")
            sys.exit(1)
    main(pr_number)
