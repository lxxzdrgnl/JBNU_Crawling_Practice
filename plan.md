# 전북대 공지사항 크롤링 + MongoDB 저장 구현 계획

## 개요
기존 Playwright 기반 크롤링 로직을 재활용하여 전북대 각종 공지사항을 크롤링하고 MongoDB에 저장하는 기능 구현

## 인증
- Google OAuth + JWT 방식 (추후 구현)

## 아키텍처
```
┌──────────────────────────────────────────────────────────┐
│                    이 프로젝트 (백엔드)                     │
│                                                          │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │ 크롤링 엔진  │   │  REST API   │   │  MCP 서버   │    │
│  │ (Playwright)│   │  (FastAPI)  │   │  (FastMCP)  │    │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘    │
│         │                 │                 │           │
│         └────────┬────────┴─────────────────┘           │
│                  ▼                                      │
│         ┌────────────────┐                              │
│         │    Services    │  ← 공통 비즈니스 로직          │
│         │ (notices, etc) │                              │
│         └────────┬───────┘                              │
│                  ▼                                      │
│            ┌─────────┐                                  │
│            │ MongoDB │                                  │
│            └─────────┘                                  │
└──────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
 ┌─────────────┐                ┌─────────────┐
 │  웹/앱 UI   │                │   Claude    │
 │ (나열/조회) │                │ (AI Agent)  │
 └─────────────┘                └─────────────┘
```

**구조**:
- **크롤링 엔진**: 공지사항 수집 → MongoDB 저장
- **Services**: 공통 로직 (검색, 조회 등)
- **REST API**: 웹/앱에서 목록 나열, 조회
- **MCP**: Claude에서 자연어로 접근

## 크롤링 대상 (11개 URL → 6개 게시판)

| 사이트 | URL | 유형 |
|--------|-----|------|
| 공과대학 공지 | `eng.jbnu.ac.kr/eng/38/notice` | ENG |
| 공과대학 신입생 | `eng.jbnu.ac.kr/freshman/34/notice` | ENG |
| CSAI 학사공지 | `csai.jbnu.ac.kr/csai/29105/subview.do` | CSAI |
| CSAI 장학공지 | `csai.jbnu.ac.kr/csai/29106/subview.do` | CSAI |
| CSAI 취업공지 | `csai.jbnu.ac.kr/csai/29107/subview.do` | CSAI |
| CSAI 행사공지 | `csai.jbnu.ac.kr/csai/29108/subview.do` | CSAI |
| CSAI 기타공지 | `csai.jbnu.ac.kr/csai/29109/subview.do` | CSAI |
| SW사업단 | `swuniv.jbnu.ac.kr/main/jbnusw?gc=605XOAS` | SWUNIV |
| 전북대 학생공지 | `www.jbnu.ac.kr/web/news/notice/sub01.do` | JBNU |
| 전북대 특강/세미나 | `www.jbnu.ac.kr/web/news/notice/sub02.do` | JBNU |
| 전북대 공모/스터디 | `www.jbnu.ac.kr/web/news/notice/sub05.do` | JBNU |

---

## MongoDB 스키마 설계

### 1. `notices` 컬렉션 (메인)

```javascript
{
  "_id": ObjectId,
  "url": "https://...",           // unique index - 중복 체크용
  "title": "공지사항 제목",
  "author": "작성자",              // 있으면 저장
  "date": "2026-01-30",           // 작성일

  // 필터링/표시용 (UI 태그에 사용)
  "board_id": ObjectId,           // boards 컬렉션 참조
  "board_name": "컴퓨터인공지능학부",  // 빠른 조회용 denormalize

  "crawled_at": ISODate           // 크롤링 시각
}
```

### 2. `boards` 컬렉션 (게시판 = UI 태그 단위)

각 게시판은 **독립적인 단위**. group은 UI 그룹화용일 뿐 계층 아님.
하나의 게시판이 **여러 URL**을 가질 수 있음 (예: CSAI 5개 게시판 → "컴퓨터인공지능학부" 하나로 표시)

```javascript
{
  "_id": ObjectId,
  "name": "컴퓨터인공지능학부",      // UI 태그에 표시될 이름

  // UI 그룹화용 (평면적, 계층 아님)
  "group": "학과",                  // "전북대", "단과대", "학과", "사업단"

  // 크롤링 설정 - 여러 URL 가능
  "urls": [
    { "url": "https://csai.jbnu.ac.kr/csai/29105/subview.do", "name": "학사공지" },
    { "url": "https://csai.jbnu.ac.kr/csai/29106/subview.do", "name": "장학공지" },
    ...
  ],
  "crawler_type": "csai",          // eng, csai, swuniv, jbnu

  "color": "#4CAF50",              // UI 태그 색상
  "is_active": true,
  "last_crawled_at": ISODate,
  "created_at": ISODate
}
```

### 3. 초기 게시판 데이터

```javascript
// ========== 전북대 그룹 ==========
{ "name": "학생공지", "group": "전북대", "urls": [...], "crawler_type": "jbnu", "color": "#2196F3" },
{ "name": "특강&세미나", "group": "전북대", "urls": [...], "crawler_type": "jbnu", "color": "#2196F3" },
{ "name": "공모/스터디", "group": "전북대", "urls": [...], "crawler_type": "jbnu", "color": "#2196F3" },

// ========== 단과대 그룹 ==========
{ "name": "공과대학", "group": "단과대", "urls": [...], "crawler_type": "eng", "color": "#9E9E9E" },

// ========== 학과 그룹 ==========
{ "name": "컴퓨터인공지능학부", "group": "학과", "urls": [...], "crawler_type": "csai", "color": "#4CAF50" },

// ========== 사업단 그룹 ==========
{ "name": "SW중심대학사업단", "group": "사업단", "urls": [...], "crawler_type": "swuniv", "color": "#FF9800" }
```

### 인덱스

```javascript
// notices
db.notices.createIndex({ "url": 1 }, { unique: true })
db.notices.createIndex({ "board_id": 1, "date": -1 })
db.notices.createIndex({ "date": -1 })
db.notices.createIndex({ "title": "text" })  // 키워드 검색용

// boards
db.boards.createIndex({ "group": 1 })
db.boards.createIndex({ "is_active": 1 })
```

---

## 파일 구조

```
app/
├── core/
│   ├── browser.py          # 기존 (수정 없음)
│   ├── config.py           # 크롤링 소스 설정 추가
│   ├── session.py          # 기존 (수정 없음)
│   └── database.py         # [신규] MongoDB 연결 관리
├── models/
│   ├── schemas.py          # 기존 스키마 확장
│   └── db_models.py        # [신규] MongoDB 모델
├── services/               # [신규] 비즈니스 로직 (REST API & MCP 공유)
│   ├── __init__.py
│   ├── notice_service.py   # 공지사항 검색/조회
│   ├── board_service.py    # 게시판 관리
│   └── crawl_service.py    # 크롤링 실행/상태
├── api/
│   ├── auth.py             # 기존 (수정 없음)
│   ├── crawler.py          # 기존 (수정 없음)
│   └── notices.py          # [신규] 공지사항 REST API
├── crawlers/               # [신규] 크롤러 모듈
│   ├── __init__.py
│   ├── base.py             # 기본 크롤러 클래스
│   ├── eng_crawler.py      # 공과대학 크롤러
│   ├── csai_crawler.py     # CSAI 크롤러
│   ├── swuniv_crawler.py   # SW사업단 크롤러
│   └── jbnu_crawler.py     # 전북대 메인 크롤러
├── main.py                 # 라우터 등록
└── mcp_server.py           # MCP 서버 (기존 확장)
```

---

## 구현 순서

### Phase 1: 크롤링 + MongoDB
1. MongoDB 연결 설정 - `app/core/database.py`
2. 모델 정의 - `app/models/db_models.py`
3. 초기 게시판 데이터 입력
4. 기본 크롤러 클래스 - `app/crawlers/base.py`
5. CSAI 크롤러 (먼저 테스트)
6. 나머지 크롤러 - eng, jbnu, swuniv
7. 크롤링 서비스 - `app/services/crawl_service.py`

### Phase 2: REST API
8. 공지사항 서비스 - `app/services/notice_service.py`
9. 공지사항 API - `app/api/notices.py`
10. 라우터 등록 - `app/main.py`

### Phase 3: MCP 서버
11. MCP 도구 추가 - `mcp_server.py` 확장

---

## REST API

```python
GET  /notices              # 목록 조회 (필터링: boards, keyword, page, limit)
GET  /notices/{notice_id}  # 단일 조회
GET  /boards               # 게시판 목록
POST /crawl                # 크롤링 실행
```

---

## MCP 도구

```python
@mcp.tool()
async def search_notices(keyword: str, boards: list[str] = None, limit: int = 10):
    """공지사항 검색 - "장학금 공지 찾아줘" """

@mcp.tool()
async def get_latest_notices(boards: list[str] = None, days: int = 7, limit: int = 20):
    """최신 공지 - "오늘 새 공지 있어?" """

@mcp.tool()
async def get_boards():
    """게시판 목록"""

@mcp.tool()
async def trigger_crawl(boards: list[str] = None):
    """크롤링 실행 - "공지 새로고침해줘" """
```

---

## 기술 스택

| 항목 | 기술 |
|------|------|
| 비동기 MongoDB | `motor` |
| 크롤링 | Playwright (기존) |
| API | FastAPI (기존) |
| MCP | FastMCP (기존) |

## 의존성 추가

```
motor==3.3.2
```

---

## 추후 구현 (나중에)
- [ ] 인증: 외부 서버 + JWT
- [ ] 키워드 알림 기능
- [ ] 사용자 구독 게시판
- [ ] 본문 크롤링 (2단계)
- [ ] 주기적 크롤링 스케줄링
- [ ] MongoDB Atlas 마이그레이션
