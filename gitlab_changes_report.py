#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta
import gitlab
from dotenv import load_dotenv
import pandas as pd
import urllib3
import warnings

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Suppress pagination warnings
warnings.filterwarnings('ignore', category=UserWarning, module='gitlab')

def load_gitlab_config():
    """Load GitLab configuration from environment variables."""
    load_dotenv(override=True)
    
    # Get common settings
    gitlab_url = os.getenv('GITLAB_URL')
    gitlab_token = os.getenv('GITLAB_TOKEN')
    project_ids = os.getenv('GITLAB_PROJECT_IDS')
    days = int(os.getenv('GITLAB_DAYS', '7'))  # Default to 7 days if not specified
    
    # Check required settings
    if not gitlab_url or not gitlab_token or not project_ids:
        print("Error: Missing required GitLab settings")
        if not gitlab_url:
            print("- GITLAB_URL is missing")
        if not gitlab_token:
            print("- GITLAB_TOKEN is missing")
        if not project_ids:
            print("- GITLAB_PROJECT_IDS is missing")
        sys.exit(1)
    
    # Split project IDs and create config for each
    projects = []
    for pid in project_ids.split(','):
        pid = pid.strip()  # Remove any whitespace
        if pid:  # Only add non-empty project IDs
            projects.append({
                'url': gitlab_url,
                'token': gitlab_token,
                'project_id': pid,
                'days': days
            })
    
    if not projects:
        print("Error: No valid project IDs found")
        sys.exit(1)
    
    return projects

def get_gitlab_client(url, token):
    """Initialize GitLab client."""
    try:
        gl = gitlab.Gitlab(url=url, private_token=token, ssl_verify=False)
        gl.auth()
        return gl
    except Exception as e:
        print(f"Error connecting to GitLab: {str(e)}")
        sys.exit(1)

def get_project_changes(gl, project_id, days=7):
    """Get project changes for the specified number of days."""
    try:
        project = gl.projects.get(project_id)
        since_date = datetime.now() - timedelta(days=days)
        
        # Get project name for report filename
        project_name = project.name.lower().replace(' ', '_')
        
        # Get commits with pagination
        commits = project.commits.list(since=since_date.isoformat(), all=True, per_page=100)
        commit_data = []
        for commit in commits:
            # Get detailed commit info including diff
            detailed_commit = project.commits.get(commit.id)
            diff = detailed_commit.diff()
            diff_summary = []
            for change in diff:
                diff_summary.append({
                    'new_path': change['new_path'],
                    'old_path': change['old_path'],
                    'new_file': change['new_file'],
                    'deleted_file': change['deleted_file'],
                    'renamed_file': change['renamed_file'],
                    'diff': change['diff']
                })
            
            commit_data.append({
                'type': 'commit',
                'id': commit.id,
                'title': commit.title,
                'author': commit.author_name,
                'date': commit.created_at,
                'diff_summary': diff_summary
            })
        
        # Get merge requests with pagination
        mrs = project.mergerequests.list(updated_after=since_date.isoformat(), state='all', per_page=100, get_all=True)
        mr_data = []
        for mr in mrs:
            mr_data.append({
                'type': 'merge_request',
                'id': mr.iid,
                'title': mr.title,
                'author': mr.author['name'],
                'state': mr.state,
                'date': mr.created_at,
                'url': mr.web_url
            })
        
        # Get issues with pagination
        issues = project.issues.list(updated_after=since_date.isoformat(), state='all', per_page=100, get_all=True)
        issue_data = []
        for issue in issues:
            issue_data.append({
                'type': 'issue',
                'id': issue.iid,
                'title': issue.title,
                'author': issue.author['name'],
                'state': issue.state,
                'date': issue.created_at,
                'url': issue.web_url
            })
        
        return {
            'project_name': project_name,
            'commits': commit_data,
            'merge_requests': mr_data,
            'issues': issue_data
        }
    except Exception as e:
        print(f"Error getting project changes: {str(e)}")
        return None

def generate_report(changes, output_file='gitlab_changes_report.md'):
    """Generate Markdown report from the changes data."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# GitLab Changes Report - {changes['project_name']}\n\n")
            
            # Write commits section
            f.write('## Commits\n\n')
            if changes['commits']:
                for commit in changes['commits']:
                    f.write(f"### {commit['title']}\n\n")
                    f.write(f"- **Commit ID**: {commit['id']}\n")
                    f.write(f"- **Author**: {commit['author']}\n")
                    f.write(f"- **Date**: {commit['date']}\n\n")
                    
                    if commit['diff_summary']:
                        f.write("#### Changes\n\n")
                        for diff in commit['diff_summary']:
                            change_type = 'New file' if diff['new_file'] else \
                                        'Deleted' if diff['deleted_file'] else \
                                        'Renamed' if diff['renamed_file'] else 'Modified'
                            
                            f.write(f"**{change_type}**: {diff['new_path']}\n\n")
                            if diff['diff']:
                                f.write("```diff\n")
                                f.write(diff['diff'])
                                f.write("\n```\n\n")
            else:
                f.write("No commits in the specified time period.\n\n")
            
            # Write merge requests section
            f.write('## Merge Requests\n\n')
            if changes['merge_requests']:
                for mr in changes['merge_requests']:
                    f.write(f"### {mr['title']}\n\n")
                    f.write(f"- **ID**: !{mr['id']}\n")
                    f.write(f"- **Author**: {mr['author']}\n")
                    f.write(f"- **State**: {mr['state']}\n")
                    f.write(f"- **Date**: {mr['date']}\n")
                    f.write(f"- **URL**: {mr['url']}\n\n")
            else:
                f.write("No merge requests in the specified time period.\n\n")
            
            # Write issues section
            f.write('## Issues\n\n')
            if changes['issues']:
                for issue in changes['issues']:
                    f.write(f"### {issue['title']}\n\n")
                    f.write(f"- **ID**: #{issue['id']}\n")
                    f.write(f"- **Author**: {issue['author']}\n")
                    f.write(f"- **State**: {issue['state']}\n")
                    f.write(f"- **Date**: {issue['date']}\n")
                    f.write(f"- **URL**: {issue['url']}\n\n")
            else:
                f.write("No issues in the specified time period.\n\n")
        
        print(f"Report generated successfully: {output_file}")
        return True
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return False

def main():
    # Load configuration for all projects
    projects_config = load_gitlab_config()
    
    for i, config in enumerate(projects_config, 1):
        # Initialize GitLab client
        gl = get_gitlab_client(config['url'], config['token'])
        
        # Get changes for the specified days
        changes = get_project_changes(gl, config['project_id'], config['days'])
        
        if changes:
            # Generate report with project name in filename
            project_name = changes['project_name']
            output_file = f'gitlab_changes_report_{project_name}.md'
            generate_report(changes, output_file)
        else:
            print(f"Failed to generate report for project {i} due to errors.")

if __name__ == "__main__":
    main() 