# GitLab Changes Report Generator

이 스크립트는 GitLab 프로젝트의 변경 사항을 추적하고 Markdown 리포트를 생성합니다.

## 기능

- 최근 커밋 이력 추적
  - 커밋 상세 정보 (ID, 작성자, 날짜)
  - 파일 변경 사항 (추가, 수정, 삭제, 이름 변경)
  - Diff 내용 포함
- Merge Request 현황 조회
  - MR 상태, 작성자, URL 정보
- Issue 현황 조회
  - Issue 상태, 작성자, URL 정보
- Markdown 형식의 리포트 생성
- 다중 프로젝트 지원
- SSL 인증서 검증 무시 지원 (자체 서명 인증서 사용 시)
- 페이지네이션 자동 처리 (대량의 데이터 조회 지원)
- 조회 기간 설정 지원

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. `.env` 파일 설정:
```
GITLAB_URL=https://your-gitlab-server
GITLAB_TOKEN=your-access-token
GITLAB_PROJECT_IDS=project1_id,project2_id
GITLAB_DAYS=7
```

## 환경 변수 설명

- `GITLAB_URL`: GitLab 서버 URL (예: https://gitlab.com)
- `GITLAB_TOKEN`: GitLab 개인 접근 토큰
- `GITLAB_PROJECT_IDS`: 대상 프로젝트 ID (콤마로 구분하여 여러 개 지정 가능)
- `GITLAB_DAYS`: 변경사항을 조회할 기간(일) (기본값: 7)

## 사용 방법

1. `.env` 파일에 필요한 설정을 입력합니다.
2. 스크립트를 실행합니다:
```bash
python gitlab_changes_report.py
```

## 출력 결과

스크립트는 각 프로젝트별로 프로젝트 이름이 포함된 리포트 파일을 생성합니다:
예: `gitlab_changes_report_project_name.md`

각 리포트는 다음 섹션들을 포함합니다:
- Commits: 최근 커밋 이력
  - 커밋 메시지
  - 커밋 상세 정보
  - 변경된 파일 목록과 diff
- Merge Requests: MR 현황
  - 제목, 상태, 작성자
  - 웹 URL
- Issues: 이슈 현황
  - 제목, 상태, 작성자
  - 웹 URL

## 주의사항

- GitLab API 토큰은 적절한 권한이 필요합니다 (최소 read_api 권한).
- 조회 기간을 지정하지 않으면 기본적으로 최근 7일간의 변경사항을 조회합니다.
- 자체 서명된 SSL 인증서를 사용하는 경우 자동으로 인증서 검증을 건너뜁니다.
- 대량의 데이터 조회 시 자동으로 페이지네이션을 처리합니다. 