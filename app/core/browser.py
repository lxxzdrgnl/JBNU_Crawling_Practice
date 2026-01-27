"""브라우저 자동화 및 크롤링 로직"""

from typing import Optional, Dict, Any, List, Tuple
from playwright.async_api import (
    async_playwright, Browser, BrowserContext, Page, TimeoutError, Playwright
)

from app.core.session import session_manager
from app.core.config import *


class BrowserManager:
    """Playwright 브라우저 관리 및 크롤링"""

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}

    # ==================== 브라우저 라이프사이클 ====================

    async def initialize(self):
        """Playwright 초기화"""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=BROWSER_HEADLESS_LOGIN
            )

    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def create_context(
        self,
        session_id: str,
        cookies: Optional[list] = None
    ) -> BrowserContext:
        """새 브라우저 컨텍스트 생성"""
        await self.initialize()

        context = await self.browser.new_context(
            viewport=BROWSER_VIEWPORT,
            user_agent=BROWSER_USER_AGENT
        )

        if cookies:
            await context.add_cookies(cookies)

        self.contexts[session_id] = context
        return context

    async def get_context(self, session_id: str) -> Optional[BrowserContext]:
        """세션의 컨텍스트 가져오기"""
        return self.contexts.get(session_id)

    async def close_context(self, session_id: str):
        """컨텍스트 종료"""
        if session_id in self.contexts:
            await self.contexts[session_id].close()
            del self.contexts[session_id]

    # ==================== 로그인 관련 ====================

    async def start_login(
        self,
        session_id: str,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """로그인 시작 (아이디/비밀번호 입력)"""
        try:
            context = await self.create_context(session_id)
            page = await context.new_page()

            # 로그인 페이지로 이동 및 폼 입력
            await self._navigate_to_login_page(page)
            await self._fill_login_form(page, username, password)
            await self._submit_login_form(page)

            # 로그인 결과 확인
            if await self._is_otp_required(page):
                return {"status": "otp_required", "message": "OTP 입력이 필요합니다"}

            if await self._is_login_successful(page):
                await self._save_session_cookies(context, username)
                return {"status": "success", "message": "로그인 성공"}

            return {"status": "error", "message": "로그인 실패. 아이디나 비밀번호를 확인하세요."}

        except TimeoutError:
            return {"status": "error", "message": "로그인 페이지 로딩 시간 초과"}
        except Exception as e:
            return {"status": "error", "message": f"로그인 중 오류: {str(e)}"}

    async def submit_otp(
        self,
        session_id: str,
        otp: str,
        username: str
    ) -> Dict[str, Any]:
        """OTP 제출"""
        try:
            context = await self.get_context(session_id)
            if not context:
                return {"status": "error", "message": "세션을 찾을 수 없습니다"}

            page = context.pages[0]
            self._log_page_info(page)

            # OTP 입력 및 제출
            await self._fill_otp(page, otp)
            await self._submit_otp_form(page)

            # 로그인 결과 확인
            if await self._is_login_successful(page):
                await self._save_session_cookies(context, username)
                return {"status": "success", "message": "로그인 성공"}

            return {"status": "error", "message": "OTP 인증 실패"}

        except TimeoutError:
            return {"status": "error", "message": "OTP 처리 시간 초과"}
        except Exception as e:
            return {"status": "error", "message": f"OTP 처리 중 오류: {str(e)}"}

    # ==================== 크롤링 관련 ====================

    async def crawl_courses(self, username: str) -> List[Dict[str, Any]]:
        """강의 목록 크롤링"""
        playwright_instance = None
        browser_instance = None

        try:
            cookies = session_manager.load_cookies(username)
            if not cookies:
                print("[ERROR] 저장된 쿠키가 없습니다")
                return []

            # 독립적인 브라우저 인스턴스 생성
            playwright_instance, browser_instance = await self._create_browser_for_crawling()
            page = await self._create_page_with_cookies(browser_instance, cookies)

            # 강의 목록 페이지로 이동 및 학기 선택
            await self._navigate_to_courses_page(page)
            await self._select_semester(page)

            # 강의 목록 추출
            courses = await self._extract_courses(page, username)

            print(f"[INFO] 총 {len(courses)}개 강의 추출 완료")
            return courses

        except Exception as e:
            print(f"[ERROR] 강의 목록 크롤링 오류: {e}")
            import traceback
            traceback.print_exc()
            return []

        finally:
            await self._cleanup_browser(browser_instance, playwright_instance)

    # ==================== 내부 헬퍼 메서드: 로그인 ====================

    async def _navigate_to_login_page(self, page: Page):
        """로그인 페이지로 이동"""
        await page.goto(LMS_BASE_URL)
        await page.wait_for_selector(SELECTOR_LOGIN_INPUT, timeout=TIMEOUT_ELEMENT_WAIT)

    async def _fill_login_form(self, page: Page, username: str, password: str):
        """로그인 폼 입력"""
        await page.fill(SELECTOR_LOGIN_INPUT, username)
        await page.fill(SELECTOR_PASSWORD_INPUT, password)

    async def _submit_login_form(self, page: Page):
        """로그인 폼 제출"""
        await page.click(SELECTOR_SUBMIT_BUTTON)
        await page.wait_for_load_state("networkidle", timeout=TIMEOUT_ELEMENT_WAIT)

    async def _is_otp_required(self, page: Page) -> bool:
        """OTP 입력이 필요한지 확인"""
        try:
            otp_input = await page.query_selector(SELECTOR_OTP_INPUT)
            return otp_input is not None
        except Exception:
            return False

    async def _is_login_successful(self, page: Page) -> bool:
        """로그인 성공 여부 확인"""
        return "login" not in page.url.lower()

    async def _save_session_cookies(self, context: BrowserContext, username: str):
        """세션 쿠키 저장"""
        cookies = await context.cookies()
        session_manager.save_cookies(username, cookies)

    def _log_page_info(self, page: Page):
        """페이지 정보 로깅 (동기 함수)"""
        # 비동기 호출이 필요한 경우 호출하는 쪽에서 await 사용
        pass

    async def _fill_otp(self, page: Page, otp: str):
        """OTP 입력"""
        await page.fill(SELECTOR_OTP_INPUT, otp)
        await page.wait_for_timeout(TIMEOUT_INPUT_DELAY)

    async def _submit_otp_form(self, page: Page):
        """OTP 폼 제출 (여러 방법 시도)"""
        try:
            # 방법 1: Enter 키
            await page.press(SELECTOR_OTP_INPUT, "Enter")
        except Exception:
            # 방법 2: 버튼 클릭
            await self._try_click_otp_button(page)

        await page.wait_for_load_state("networkidle", timeout=TIMEOUT_OTP_SUBMIT)

    async def _try_click_otp_button(self, page: Page):
        """OTP 제출 버튼 클릭 시도"""
        for selector in OTP_SUBMIT_SELECTORS:
            try:
                await page.click(selector, timeout=1000)
                return
            except Exception:
                continue

    # ==================== 내부 헬퍼 메서드: 크롤링 ====================

    async def _create_browser_for_crawling(self) -> Tuple[Playwright, Browser]:
        """크롤링용 독립 브라우저 생성"""
        playwright_instance = await async_playwright().start()
        browser_instance = await playwright_instance.chromium.launch(
            headless=BROWSER_HEADLESS_CRAWL
        )
        return playwright_instance, browser_instance

    async def _create_page_with_cookies(
        self,
        browser: Browser,
        cookies: list
    ) -> Page:
        """쿠키를 포함한 새 페이지 생성"""
        context = await browser.new_context(
            viewport=BROWSER_VIEWPORT,
            user_agent=BROWSER_USER_AGENT
        )
        await context.add_cookies(cookies)
        return await context.new_page()

    async def _navigate_to_courses_page(self, page: Page):
        """강의 목록 페이지로 이동"""
        print(f"[DEBUG] 페이지 이동: {LMS_BASE_URL}")
        await page.goto(LMS_BASE_URL, timeout=TIMEOUT_PAGE_LOAD)
        await page.wait_for_load_state("networkidle", timeout=TIMEOUT_PAGE_LOAD)
        print(f"[DEBUG] 현재 URL: {page.url}")

    async def _select_semester(self, page: Page):
        """학기 선택"""
        print("[DEBUG] 학기 선택 시도...")

        dropdown = await self._find_semester_dropdown(page)
        if not dropdown:
            print("[WARNING] 학기 선택 드롭다운을 찾을 수 없습니다")
            return

        await self._log_semester_options(page, dropdown)
        selected = await self._select_2025_semester_2(page, dropdown)

        if selected:
            await self._wait_for_semester_change(page)
        else:
            print("[WARNING] 2025년 2학기 선택 실패. 현재 선택된 학기 사용")

    async def _find_semester_dropdown(self, page: Page):
        """학기 선택 드롭다운 찾기"""
        for selector in DROPDOWN_SELECTORS:
            try:
                dropdown = await page.query_selector(selector)
                if dropdown:
                    print(f"[DEBUG] 드롭다운 발견: {selector}")
                    return dropdown
            except Exception:
                continue
        return None

    async def _log_semester_options(self, page: Page, dropdown):
        """학기 옵션 로깅"""
        current_value = await page.evaluate("(element) => element.value", dropdown)
        print(f"[DEBUG] 현재 선택된 학기: {current_value}")

        options = await page.evaluate("""
            (element) => Array.from(element.options).map(opt => ({
                value: opt.value,
                text: opt.text
            }))
        """, dropdown)
        print(f"[DEBUG] 사용 가능한 학기 옵션: {options}")

    async def _select_2025_semester_2(self, page: Page, dropdown) -> bool:
        """2025년 2학기 선택"""
        # 직접 value로 선택 시도
        for val in SEMESTER_VALUES_2025_2:
            try:
                await page.select_option("select", value=val)
                print(f"[DEBUG] 학기 선택 성공: {val}")
                return True
            except Exception:
                continue

        # text 매칭으로 선택 시도
        options = await page.evaluate("""
            (element) => Array.from(element.options).map(opt => ({
                value: opt.value,
                text: opt.text
            }))
        """, dropdown)

        for opt in options:
            if "2025" in opt["text"] and "2" in opt["text"]:
                try:
                    await page.select_option("select", value=opt["value"])
                    print(f"[DEBUG] 학기 선택 성공 (text 매칭): {opt['text']}")
                    return True
                except Exception:
                    continue

        return False

    async def _wait_for_semester_change(self, page: Page):
        """학기 변경 후 페이지 로딩 대기"""
        print("[DEBUG] 강의 목록 로딩 대기 중...")
        await page.wait_for_timeout(TIMEOUT_SEMESTER_LOAD)
        await page.wait_for_load_state("networkidle", timeout=TIMEOUT_OTP_SUBMIT)
        await page.wait_for_timeout(TIMEOUT_CONTENT_LOAD)
        print("[DEBUG] 학기 선택 후 페이지 로딩 완료")

    async def _extract_courses(
        self,
        page: Page,
        username: str
    ) -> List[Dict[str, Any]]:
        """강의 목록 추출"""
        course_elements = await page.query_selector_all(SELECTOR_COURSE_CARD)
        print(f"[DEBUG] {len(course_elements)}개 강의 카드 발견")

        if not course_elements:
            await self._save_debug_files(page, username)
            return []

        courses = []
        for idx, card in enumerate(course_elements):
            course = await self._extract_single_course(card, idx)
            if course:
                courses.append(course)
                print(f"[DEBUG] 강의 추출: {course['name']} - {course['professor']}")

        return courses

    async def _extract_single_course(
        self,
        card,
        idx: int
    ) -> Optional[Dict[str, Any]]:
        """개별 강의 정보 추출"""
        try:
            title = await card.get_attribute("title")
            professor = await self._extract_professor_name(card)

            if title:
                return {
                    "id": f"course_{idx}",
                    "name": title.strip(),
                    "professor": professor,
                    "semester": "2학기",
                    "year": 2025
                }
        except Exception as e:
            print(f"[WARNING] 강의 카드 파싱 오류: {e}")

        return None

    async def _extract_professor_name(self, card) -> Optional[str]:
        """교수명 추출"""
        try:
            parent = await card.evaluate_handle("(element) => element.parentElement")
            prof_div = await parent.query_selector(SELECTOR_PROFESSOR_DIV)
            if prof_div:
                professor = await prof_div.inner_text()
                return professor.strip()
        except Exception as e:
            print(f"[DEBUG] 교수명 추출 실패: {e}")

        return None

    async def _save_debug_files(self, page: Page, username: str):
        """디버그 파일 저장"""
        if not DEBUG_SAVE_SCREENSHOT and not DEBUG_SAVE_HTML:
            return

        print("[WARNING] 강의 카드를 찾을 수 없습니다. 디버그 파일을 저장합니다.")

        if DEBUG_SAVE_SCREENSHOT:
            screenshot_path = f"{DEBUG_STORAGE_PATH}/debug_screenshot_{username}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"[DEBUG] 스크린샷 저장: {screenshot_path}")

        if DEBUG_SAVE_HTML:
            html_content = await page.content()
            html_path = f"{DEBUG_STORAGE_PATH}/debug_html_{username}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"[DEBUG] HTML 저장: {html_path}")
            print(f"[DEBUG] HTML 길이: {len(html_content)} 문자")

    async def _cleanup_browser(
        self,
        browser_instance: Optional[Browser],
        playwright_instance: Optional[Playwright]
    ):
        """브라우저 정리"""
        try:
            if browser_instance:
                await browser_instance.close()
                print("[DEBUG] 브라우저 종료 완료")
            if playwright_instance:
                await playwright_instance.stop()
                print("[DEBUG] Playwright 종료 완료")
        except Exception as e:
            print(f"[WARNING] 브라우저 정리 중 오류: {e}")


# 전역 브라우저 매니저 인스턴스
browser_manager = BrowserManager()
