"""애플리케이션 설정 및 상수"""

# LMS 사이트 설정
LMS_BASE_URL = "https://ieilms.jbnu.ac.kr/"

# 브라우저 설정
BROWSER_VIEWPORT = {"width": 1280, "height": 720}
BROWSER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
BROWSER_HEADLESS_LOGIN = False  # 로그인 시 브라우저 표시 (디버깅용)
BROWSER_HEADLESS_CRAWL = True   # 크롤링 시 headless 모드

# 타임아웃 설정 (밀리초)
TIMEOUT_PAGE_LOAD = 30000        # 30초
TIMEOUT_ELEMENT_WAIT = 10000     # 10초
TIMEOUT_OTP_SUBMIT = 15000       # 15초
TIMEOUT_INPUT_DELAY = 500        # 0.5초
TIMEOUT_SEMESTER_LOAD = 3000     # 3초 (학기 선택 후 대기)
TIMEOUT_CONTENT_LOAD = 2000      # 2초 (동적 컨텐츠 로딩)

# HTML 셀렉터
SELECTOR_LOGIN_INPUT = "input[name='login']"
SELECTOR_PASSWORD_INPUT = "input[name='passwd']"
SELECTOR_SUBMIT_BUTTON = "button[type='submit'], input[type='submit']"
SELECTOR_OTP_INPUT = "input[name='googleOTP']"
SELECTOR_COURSE_CARD = ".leftGroupMenu_div"
SELECTOR_PROFESSOR_DIV = "div[style*='color:gray']"

# 드롭다운 셀렉터 (우선순위 순)
DROPDOWN_SELECTORS = [
    "select",
    "select[class*='semester']",
    "select[class*='year']",
    "#semester",
    "#yearSemester",
    "[name*='semester']",
    "[name*='year']"
]

# OTP 제출 버튼 셀렉터 (우선순위 순)
OTP_SUBMIT_SELECTORS = [
    "button[type='submit']",
    "input[type='submit']",
    "button:has-text('확인')",
    "button:has-text('로그인')",
    "input[value='확인']",
    "input[value='로그인']",
    "form button",
    ".btn-submit",
    "#btnSubmit"
]

# 학기 선택 가능한 값들
SEMESTER_VALUES_2025_2 = ["2025-2", "20252", "2025_2", "2025년 2학기"]

# 세션 및 쿠키 설정
COOKIE_STORAGE_DIR = "storage/cookies"
COOKIE_VALIDITY_DAYS = 7  # 쿠키 유효 기간 (일)

# 디버그 설정
DEBUG_SAVE_SCREENSHOT = True
DEBUG_SAVE_HTML = True
DEBUG_STORAGE_PATH = "storage"
