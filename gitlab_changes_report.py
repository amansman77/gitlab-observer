#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta
import gitlab
from dotenv import load_dotenv
import pandas as pd
import urllib3
import warnings
import json
from openai import OpenAI
import discord
from discord import SyncWebhook

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

def analyze_changes_with_llm(changes):
    """Analyze changes using OpenAI's GPT model."""
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Prepare the data for analysis
        analysis_prompt = {
            "project_name": changes['project_name'],
            "commit_count": len(changes['commits']),
            "mr_count": len(changes['merge_requests']),
            "issue_count": len(changes['issues']),
            "commits": [
                {
                    "author": commit['author'],
                    "title": commit['title'],
                    "date": commit['date'],
                    "changes": [
                        {
                            "type": "New file" if diff['new_file'] else 
                                   "Deleted" if diff['deleted_file'] else 
                                   "Renamed" if diff['renamed_file'] else "Modified",
                            "path": diff['new_path'],
                            "diff": diff['diff']
                        } for diff in commit['diff_summary']
                    ]
                } for commit in changes['commits']
            ],
            "issues": [
                {
                    "author": issue['author'],
                    "title": issue['title'],
                    "state": issue['state'],
                    "date": issue['date']
                } for issue in changes['issues']
            ],
            "merge_requests": [
                {
                    "author": mr['author'],
                    "title": mr['title'],
                    "state": mr['state'],
                    "date": mr['date']
                } for mr in changes['merge_requests']
            ]
        }

        system_prompt = """당신은 개발팀 활동을 분석하는 전문가입니다. 제공된 GitLab 프로젝트 변경사항을 분석하여 다음 내용을 한국어로 제공해주세요:

1. 프로젝트 현황 요약
   - 전체 이슈/커밋/MR 수
   - 주요 진행 중인 작업 영역
   - 커밋 내용 요약 (주요 변경사항)

2. 팀원별 활동 현황
   - 각 팀원이 담당하고 있는 주요 업무
   - 진행 중인 작업과 완료된 작업 구분
   - 각 팀원의 커밋 및 변경사항 요약

3. 주요 개발 영역
   - 현재 중점적으로 개발 중인 기능/영역
   - 진행 중인 중요 이슈들
   - 코드 변경의 주요 내용

전문적이고 간단명료한 톤을 유지하면서, 실질적인 통찰을 제공해주세요.
특히 커밋 내용과 코드 변경사항을 자세히 분석하여 실제 개발 진행 상황을 구체적으로 설명해주세요."""

        user_prompt = f"다음 GitLab 프로젝트 변경사항을 분석해주세요:\n{json.dumps(analysis_prompt, indent=2, ensure_ascii=False)}"

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error analyzing changes with LLM: {str(e)}")
        return None

def generate_report(changes, output_file='gitlab_changes_report.md'):
    """Generate Markdown report from the changes data."""
    try:
        # 변경사항이 없으면 리포트를 생성하지 않음 (커밋, 머지 리퀘스트, 이슈 모두 체크)
        if not changes['commits'] and not changes['merge_requests'] and not changes['issues']:
            print(f"프로젝트 {changes['project_name']}에 변경사항이 없어 리포트를 생성하지 않습니다.")
            return False
            
        # Get LLM analysis
        analysis = analyze_changes_with_llm(changes)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {changes['project_name']} 프로젝트 현황 리포트\n\n")
            
            # Write AI Analysis section
            if analysis:
                f.write(analysis)
                f.write('\n\n')
            
            # Write summary section if there are any commits
            if changes['commits']:
                f.write('## 커밋 요약\n\n')
                for commit in changes['commits']:
                    f.write(f"- **{commit['author']}**: {commit['title']}\n")
                f.write('\n')
            
            # Write merge requests summary if there are any
            if changes['merge_requests']:
                f.write('## 머지 리퀘스트 요약\n\n')
                for mr in changes['merge_requests']:
                    f.write(f"- **{mr['author']}**: {mr['title']} ({mr['state']})\n")
                f.write('\n')
        
        print(f"Report generated successfully: {output_file}")
        return True
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return False

def send_to_discord(report_file, days):
    """Send the report to Discord using webhook."""
    try:
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            print("Discord webhook URL not configured, skipping Discord notification")
            return False

        webhook = SyncWebhook.from_url(webhook_url)
        
        # 파일이 존재하는지 확인
        if not os.path.exists(report_file):
            print(f"Report file not found: {report_file}")
            return False
            
        # 리포트 파일 읽기
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 프로젝트 이름 추출 (파일명에서)
        project_name = os.path.basename(report_file).replace('gitlab_changes_report_', '').replace('.md', '')
            
        # 제목 메시지 전송
        title_message = f"📊 **GitLab 일일 리포트 - {project_name}**\n"
        title_message += f"({days}일 동안의 변경사항)"
        webhook.send(content=title_message)
        
        # 파일 전송
        with open(report_file, 'rb') as f:
            webhook.send(file=discord.File(f, filename=os.path.basename(report_file)))
            
        print(f"Successfully sent report to Discord: {report_file}")
        return True
        
    except Exception as e:
        print(f"Error sending report to Discord: {str(e)}")
        return False

def main():
    # Load configuration for all projects
    projects_config = load_gitlab_config()
    
    print(f"\n프로젝트 설정 확인: {len(projects_config)}개 프로젝트 발견")
    
    reports_generated = False  # 리포트 생성 여부를 추적
    
    for i, config in enumerate(projects_config, 1):
        print(f"\n프로젝트 {i} 처리 중 (ID: {config['project_id']})...")
        try:
            # Initialize GitLab client
            gl = get_gitlab_client(config['url'], config['token'])
            
            # Get changes for the specified days
            changes = get_project_changes(gl, config['project_id'], config['days'])
            
            if changes:
                # Generate report with project name in filename
                project_name = changes['project_name']
                output_file = f'gitlab_changes_report_{project_name}.md'
                print(f"- 프로젝트 이름: {project_name}")
                if generate_report(changes, output_file):
                    reports_generated = True
                    # 리포트가 생성되면 Discord로 전송
                    send_to_discord(output_file, config['days'])
            else:
                print(f"- 프로젝트 {config['project_id']} 처리 중 오류 발생")
        except Exception as e:
            print(f"- 프로젝트 {config['project_id']} 처리 중 예외 발생: {str(e)}")
    
    # 모든 프로젝트에서 변경사항이 없었다면 종료 코드 1을 반환
    if not reports_generated:
        print("\n모든 프로젝트에서 변경사항이 없어 리포트가 생성되지 않았습니다.")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main() 