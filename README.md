# JBNU LMS Crawler API

전북대학교 스마트학습관리시스템(ieLMS) 크롤링 API 서버

## 특징

- **Playwright 기반**: 최신 브라우저 자동화 도구 사용
- **OTP 지원**: Google OTP 인증 처리
- **세션 관리**: 쿠키 저장으로 재로그인 불필요
- **FastAPI**: 빠르고 현대적인 API 프레임워크
- **MCP 확장 가능**: 향후 Claude와 통합 가능한 구조

## 설치

```bash
# 패키지 설치
uv pip install -r requirements.txt

# Playwright 브라우저 설치
uv run playwright install chromium
```

## 실행

```bash
# 서버 시작
uv run python main.py

# 또는
uv run uvicorn app.main:app --reload
```

서버가 시작되면:
- API 문서: http://localhost:8000/docs
- 서버 주소: http://localhost:8000

## API 사용법

### 1. 로그인 시작

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "202012345",
    "password": "your_password"
  }'
```

**응답 (OTP 필요한 경우):**
```json
{
  "status": "otp_required",
  "session_id": "abc-123-def",
  "message": "OTP 입력이 필요합니다"
}
```

### 2. OTP 제출

```bash
curl -X POST "http://localhost:8000/auth/submit-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123-def",
    "otp": "123456"
  }'
```

**응답:**
```json
{
  "status": "success",
  "token": "token_abc-123-def",
  "message": "로그인 성공"
}
```

### 3. 강의 목록 조회
(편의상 25년 2학기로 크롤링하게 설정해놓았음)
```bash
curl -X GET "http://localhost:8000/courses/202118039" \
  -H "Authorization: Bearer token_159c0b9d-3659-46cd-94e1-d765e3f96699"
```

**응답 예시 (실제 크롤링 결과):**
```json
{
  "courses": [
    {
      "id": "course_0",
      "name": "2025-2학기 리눅스프로그래밍(4분반)",
      "professor": "박순찬",
      "semester": "2학기",
      "year": 2025
    },
    {
      "id": "course_1",
      "name": "2025-2학기 클라우드컴퓨팅(2분반)",
      "professor": "박현찬",
      "semester": "2학기",
      "year": 2025
    },
    {
      "id": "course_2",
      "name": "2025-2학기 웹서비스설계(3분반)",
      "professor": "이경수",
      "semester": "2학기",
      "year": 2025
    },
    {
      "id": "course_3",
      "name": "2025-2학기 초급프로젝트(1분반)",
      "professor": "이경수",
      "semester": "2학기",
      "year": 2025
    },
    {
      "id": "course_4",
      "name": "2025-2학기 데이터마이닝(1분반)",
      "professor": "송현제",
      "semester": "2학기",
      "year": 2025
    },
    {
      "id": "course_5",
      "name": "2025-2학기 소프트웨어공학(2분반)",
      "professor": "안동언",
      "semester": "2학기",
      "year": 2025
    }
  ]
}
```

### 4. 로그아웃

```bash
curl -X DELETE "http://localhost:8000/auth/logout/202012345"
```

## MCP 서버 (Claude와 통합)

MCP(Model Context Protocol) 서버를 통해 **Claude가 직접 LMS를 크롤링**할 수 있습니다.

### MCP 서버 실행

```bash
# FastAPI 서버와 별개로 실행
uv run python mcp_server.py
```

### 사용 가능한 MCP 도구

Claude가 사용할 수 있는 도구들:

1. **login_to_lms** - LMS 로그인 시작
   ```python
   login_to_lms(username="202118039", password="your_password")
   ```

2. **submit_otp** - OTP 제출
   ```python
   submit_otp(session_id="...", otp="123456")
   ```

3. **get_lms_courses** - 강의 목록 조회
   ```python
   get_lms_courses(username="202118039")
   ```

4. **logout_from_lms** - 로그아웃
   ```python
   logout_from_lms(username="202118039")
   ```

5. **check_login_status** - 로그인 상태 확인
   ```python
   check_login_status(username="202118039")
   ```

### 사용 예시

**사용자 → Claude:**
> "내 전북대 강의 목록 보여줘. 학번은 202118039이야."

**Claude의 자동 동작:**
1. `check_login_status(username="202118039")` - 로그인 상태 확인
2. 로그인이 안되어 있으면 비밀번호 요청
3. `login_to_lms(username="202118039", password="***")` - 로그인 시작
4. 사용자에게 OTP 요청
5. `submit_otp(session_id="...", otp="123456")` - OTP 제출
6. `get_lms_courses(username="202118039")` - 강의 목록 조회
7. 결과를 보기 좋게 정리해서 보여줌


## 프로젝트 구조

```
Crawling/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 메인
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # 인증 API
│   │   └── crawler.py       # 크롤링 API
│   ├── core/
│   │   ├── __init__.py
│   │   ├── browser.py       # Playwright 브라우저 관리
│   │   ├── config.py        # 설정 및 상수
│   │   └── session.py       # 세션 및 쿠키 관리
│   └── models/
│       ├── __init__.py
│       └── schemas.py       # Pydantic 데이터 모델
├── storage/
│   └── cookies/             # 쿠키 저장 폴더 (자동 생성)
├── main.py                  # FastAPI 서버 실행
├── mcp_server.py            # MCP 서버 (Claude 통합)
├── requirements.txt         # Python 패키지 목록
├── pyproject.toml
├── .gitignore
└── README.md
```

## 작동 원리

### 로그인 플로우

1. **첫 로그인**:
   - 사용자가 `/auth/login`으로 아이디/비밀번호 전송
   - 서버가 headless 브라우저로 로그인 시도
   - OTP 필요시 `session_id` 반환
   - 사용자가 `/auth/submit-otp`로 OTP 전송
   - 로그인 성공 시 쿠키를 `storage/cookies/{username}_cookies.json`에 저장

2. **이후 접근**:
   - 저장된 쿠키로 자동 로그인
   - 쿠키는 7일간 유효

### 보안

- 쿠키 파일은 `.gitignore`에 포함되어 Git에 업로드되지 않음
- 실제 서비스에서는 JWT 토큰 사용 권장
- HTTPS 사용 권장

## 개발 모드

- `browser.py`에서 `headless=False`로 설정하면 브라우저가 보임 (디버깅용)
- 프로덕션에서는 `headless=True`로 변경

## 완료된 기능

- [x] Playwright 기반 브라우저 자동화
- [x] Google OTP 인증 처리
- [x] 세션 쿠키 저장 및 재사용
- [x] 학기 선택 (드롭다운 자동 선택)
- [x] 강의 목록 크롤링 (제목, 교수명, 학기 정보)
- [x] FastAPI REST API 구현
- [x] Swagger UI 문서 자동 생성
- [x] MCP 서버 구현 (Claude 통합)
- [x] 코드 구조 개선 (설정 분리, 함수 분리)


## 테스트 결과

### 성공 사례 (2026-01-28)

**테스트 환경:**
- OS: Linux 6.14.0-37-generic
- Python: 3.13
- Playwright: 1.57.0
- 테스트 계정: 202118039

**로그인 플로우:**
1. ✅ 아이디/비밀번호 입력 성공
2. ✅ Google OTP 인증 성공
3. ✅ 세션 쿠키 저장 성공

**강의 목록 크롤링:**
- ✅ 2025년 2학기 자동 선택
- ✅ 6개 강의 정상 크롤링
- ✅ 강의명, 교수명 정확히 추출
- 소요 시간: 약 5-8초

## 주의사항

- 이 도구는 개인 용도로만 사용하세요
- 학교 서버에 과도한 부하를 주지 않도록 주의하세요
- 개인정보(쿠키, 비밀번호)를 안전하게 관리하세요
- 쿠키 파일(`storage/cookies/`)은 절대 Git에 커밋하지 마세요
