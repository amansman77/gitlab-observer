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
- AI 기반 변경사항 분석
  - 변경사항 요약 및 인사이트
  - 개발 패턴 및 트렌드 분석
  - 잠재적 문제점 식별
  - 개발팀을 위한 제안사항
- Markdown 형식의 리포트 생성
- 다중 프로젝트 지원
- SSL 인증서 검증 무시 지원 (자체 서명 인증서 사용 시)
- 페이지네이션 자동 처리 (대량의 데이터 조회 지원)
- 조회 기간 설정 지원
- 디스코드 자동 알림
  - 리포트 자동 전송
  - 프로젝트별 변경사항 요약
  - 마크다운 파일 첨부

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
OPENAI_API_KEY=your-openai-api-key
DISCORD_WEBHOOK_URL=your-discord-webhook-url
```

## 환경 변수 설명

- `GITLAB_URL`: GitLab 서버 URL (예: https://gitlab.com)
  - 프로토콜(https://)을 포함한 전체 URL
  - 포트가 있는 경우 포트 번호도 포함 (예: https://gitlab.example.com:8443)

- `GITLAB_TOKEN`: GitLab 개인 접근 토큰
  - GitLab > User Settings > Access Tokens에서 생성
  - 필요한 권한: api, read_api, read_repository
  - 토큰 생성 시 만료일 설정 가능 (권장: 90일)

- `GITLAB_PROJECT_IDS`: 대상 프로젝트 ID (콤마로 구분하여 여러 개 지정 가능)
  - 프로젝트 ID는 GitLab 프로젝트 페이지에서 확인 가능
  - 여러 프로젝트 지정 시 콤마로 구분 (예: 123,456,789)
  - 공백이 있는 경우 자동으로 제거됨

- `GITLAB_DAYS`: 변경사항을 조회할 기간(일) (기본값: 7)
  - 양의 정수로 지정
  - 미지정 시 7일로 자동 설정

- `OPENAI_API_KEY`: OpenAI API 키
  - OpenAI 웹사이트에서 발급
  - AI 분석 기능 사용을 위해 필요
  - 환경변수 미설정 시 AI 분석 기능 비활성화

- `DISCORD_WEBHOOK_URL`: 디스코드 웹훅 URL
  - 디스코드 채널 설정 > 연동 > 웹후크에서 생성
  - 리포트 자동 전송을 위해 필요
  - 환경변수 미설정 시 디스코드 알림 비활성화

### .env 파일 예시

1. 단일 프로젝트 설정:
```
GITLAB_URL=https://gitlab.example.com:8443
GITLAB_TOKEN=glpat-XXXXXXXXXXXXXXXXX
GITLAB_PROJECT_IDS=123
GITLAB_DAYS=7
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXX
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

2. 다중 프로젝트 설정:
```
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat-XXXXXXXXXXXXXXXXX
GITLAB_PROJECT_IDS=123,456,789
GITLAB_DAYS=14
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXX
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## 디스코드 웹훅 설정 방법

1. 디스코드 채널 설정 열기
   - 채널 이름 옆 설정 아이콘(⚙️) 클릭 또는
   - 채널 이름 우클릭 → '채널 설정' 선택

2. 왼쪽 메뉴에서 '연동' 선택

3. '웹후크 만들기' 버튼 클릭

4. 웹후크 설정:
   - 이름 설정 (예: GitLab Report Bot)
   - 아이콘 선택 (선택사항)

5. '웹후크 URL 복사' 버튼으로 URL 복사

6. 복사한 URL을 `.env` 파일의 `DISCORD_WEBHOOK_URL`에 붙여넣기

## 사용 방법

1. `.env` 파일에 필요한 설정을 입력합니다.
2. 스크립트를 실행합니다:
```bash
python gitlab_changes_report.py
```

## 출력 결과

스크립트는 각 프로젝트별로 다음과 같이 결과를 생성합니다:

1. 마크다운 리포트 파일 (`gitlab_changes_report_project_name.md`):
   - Commits: 최근 커밋 이력
   - Merge Requests: MR 현황
   - Issues: 이슈 현황

2. 디스코드 알림:
   - 리포트 제목과 기간 정보
   - 마크다운 파일 첨부

## 주의사항

- GitLab API 토큰은 적절한 권한이 필요합니다 (최소 read_api 권한).
- 조회 기간을 지정하지 않으면 기본적으로 최근 7일간의 변경사항을 조회합니다.
- 자체 서명된 SSL 인증서를 사용하는 경우 자동으로 인증서 검증을 건너뜁니다.
- 대량의 데이터 조회 시 자동으로 페이지네이션을 처리합니다.
- 변경사항이 없는 경우 리포트가 생성되지 않으며, 디스코드 알림도 발송되지 않습니다. 