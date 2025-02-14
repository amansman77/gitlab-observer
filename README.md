# GitLab Changes Report Generator

이 스크립트는 GitLab 프로젝트의 변경 사항을 추적하고 Markdown 리포트를 생성합니다.

## 기능

- 최근 커밋 이력 추적
- Merge Request 현황 조회
- Issue 현황 조회
- Markdown 형식의 리포트 생성
- 다중 프로젝트 지원

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. `.env` 파일 설정:

단일 프로젝트 설정:
- `GITLAB_URL`: GitLab 서버 URL (예: https://gitlab.com)
- `GITLAB_TOKEN`: GitLab 개인 접근 토큰
- `GITLAB_PROJECT_ID`: 대상 프로젝트 ID

다중 프로젝트 설정:
- `GITLAB_NUM_PROJECTS`: 모니터링할 프로젝트 수
- 첫 번째 프로젝트: 위와 동일한 변수명 사용
- 두 번째 이상의 프로젝트: 변수명 뒤에 _2, _3 등의 접미사 추가
  - 예: `GITLAB_URL_2`, `GITLAB_TOKEN_2`, `GITLAB_PROJECT_ID_2`

## 사용 방법

1. `.env` 파일에 필요한 설정을 입력합니다.
2. 스크립트를 실행합니다:
```bash
python gitlab_changes_report.py
```

## 출력 결과

스크립트는 각 프로젝트별로 다음과 같은 파일을 생성합니다:
- 단일 프로젝트: `gitlab_changes_report.md`
- 다중 프로젝트: `gitlab_changes_report_1.md`, `gitlab_changes_report_2.md` 등

각 리포트는 다음 섹션들을 포함합니다:
- Commits: 최근 커밋 이력
- Merge Requests: MR 현황
- Issues: 이슈 현황

## 주의사항

- GitLab API 토큰은 적절한 권한이 필요합니다.
- 기본적으로 최근 7일간의 변경사항을 조회합니다. 