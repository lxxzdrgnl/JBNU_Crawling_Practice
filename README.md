# JBNU Notice Crawler

전북대학교 공지사항 크롤링 API / MCP 서버

## 지원 게시판

| slug | 게시판 | 그룹 | 사이트 |
|------|--------|------|--------|
| student | 학생공지 | 전북대 | www.jbnu.ac.kr |
| seminar | 특강&세미나 | 전북대 | www.jbnu.ac.kr |
| study | 공모/스터디 | 전북대 | www.jbnu.ac.kr |
| eng | 공과대학 | 단과대 | eng.jbnu.ac.kr |
| csai | 컴퓨터인공지능학부 | 학과 | csai.jbnu.ac.kr |
| swuniv | SW중심대학사업단 | 사업단 | swuniv.jbnu.ac.kr |

## 기술 스택

- **Playwright** - 헤드리스 브라우저 크롤링
- **FastAPI** - REST API 서버
- **FastMCP** - MCP 서버 (Claude 연동)
- **Motor** - 비동기 MongoDB 드라이버
- **MongoDB** - 공지사항 저장소

## 설치

```bash
# 패키지 설치
uv sync

# Playwright 브라우저 설치
uv run playwright install chromium
```

### MongoDB 실행

```bash
docker compose up -d
```

## 실행

```bash
# FastAPI 서버
uv run python main.py

# MCP 서버 (Claude 연동)
uv run python main.py --mcp
```

- API 문서: http://localhost:8000/docs

## API

### 공지사항 조회

```bash
# 전체 최신 공지
curl "http://localhost:8000/notices"

# 특정 게시판 (csai, swuniv 등)
curl "http://localhost:8000/notices?boards=csai,swuniv"

# 최근 7일
curl "http://localhost:8000/notices?days=7&limit=50"

# 키워드 검색
curl "http://localhost:8000/notices/search?keyword=장학금"

# 단일 공지 상세
curl "http://localhost:8000/notices/{notice_id}"
```

### 게시판 목록

```bash
curl "http://localhost:8000/notices/boards"
curl "http://localhost:8000/notices/boards/grouped"
```

### 크롤링 실행

```bash
# 전체 크롤링
curl -X POST "http://localhost:8000/notices/crawl"

# 특정 게시판만
curl -X POST "http://localhost:8000/notices/crawl?boards=csai"
```

## MCP 서버 (Claude 연동)

### Claude Desktop 설정

`claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "jbnu-notices": {
      "command": "uv",
      "args": ["run", "python", "main.py", "--mcp"],
      "cwd": "/path/to/Crawling"
    }
  }
}
```

### MCP 도구

| 도구 | 설명 |
|------|------|
| `get_latest_notices` | 최신 공지사항 조회 |
| `search_jbnu_notices` | 키워드 검색 |
| `list_notice_boards` | 게시판 목록 |
| `trigger_notice_crawl` | 크롤링 실행 |

## 프로젝트 구조

```
Crawling/
├── app/
│   ├── main.py                  # FastAPI 앱
│   ├── config.py                # 설정 (환경변수/.env)
│   ├── api/
│   │   └── notices.py           # 공지사항 REST API
│   ├── core/
│   │   └── database.py          # MongoDB 연결/인덱스
│   ├── crawlers/
│   │   ├── base.py              # 크롤러 베이스 클래스
│   │   ├── csai_crawler.py      # 컴퓨터인공지능학부
│   │   ├── jbnu_crawler.py      # 전북대 메인
│   │   ├── eng_crawler.py       # 공과대학 (Vue SPA)
│   │   └── swuniv_crawler.py    # SW중심대학사업단
│   ├── models/
│   │   └── db_models.py         # MongoDB 문서 모델
│   └── services/
│       ├── crawl_service.py     # 크롤링 서비스
│       └── notice_service.py    # 공지사항 조회 서비스
├── main.py                      # 서버 실행 진입점
├── mcp_server.py                # MCP 서버
├── docker-compose.yml           # MongoDB
├── pyproject.toml
└── requirements.txt
```

## 크롤러 구조

모든 크롤러는 `BaseCrawler`를 상속하며, 사이트별로 셀렉터와 동작을 오버라이드합니다.

- **메모리 효율**: `parse_list`가 async generator로 페이지 단위 yield
- **듀얼 탭**: 목록(`self.page`)과 상세(`self.detail_page`) 분리
- **테이블 변환**: HTML 테이블을 파이프 구분 텍스트로 변환 (AI 가독성 최적화)
- **자동 중단**: 연속 2페이지 새 공지 없으면 크롤링 중단 (업데이트 시 효율적)
- **콘텐츠 정제**: `\xa0` 제거, 불필요한 줄바꿈 정리

## 환경변수

`.env` 파일 또는 환경변수로 설정:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=jbnu_notices
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```
