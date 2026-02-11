"""
기본 크롤러 클래스
모든 사이트별 크롤러는 이 클래스를 상속합니다.
"""
import re
import logging
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Browser, Page
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
from bson import ObjectId

from app.core.database import Database

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """기본 크롤러 클래스"""

    row_selector: str = "table tbody tr"
    base_domain: str = ""
    pagination_param: str = "page"

    # 상세 페이지 선택자
    content_selector: str = ".view-content, .board-view-content, article, .contents"
    attachment_selector: str = "a[href*='download'], a[href*='file'], .file-list a, .attachFile a"

    def __init__(self, board_id: ObjectId, board_name: str):
        self.board_id = board_id
        self.board_name = board_name
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None          # 목록 페이지 전용
        self.detail_page: Optional[Page] = None    # 상세 페이지 전용

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        self.detail_page = await self.browser.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.detail_page:
            await self.detail_page.close()
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    @abstractmethod
    async def parse_row(self, row, base_url: str) -> Optional[Dict[str, Any]]:
        """목록에서 단일 행 파싱 - 각 크롤러가 구현"""
        pass

    async def _extract_content(self, selector: str) -> str:
        """DOM에서 본문 추출 (표→파이프 구분, AI/MCP 가독성 최적화)"""
        content = await self.detail_page.evaluate("""(selector) => {
            const el = document.querySelector(selector);
            if (!el) return '';
            const clone = el.cloneNode(true);

            // table → 파이프 구분 텍스트 (멀티라인 셀 확장)
            clone.querySelectorAll('table').forEach(table => {
                let text = '';
                table.querySelectorAll('tr').forEach(row => {
                    const cells = [...row.querySelectorAll('td, th')];
                    const cellLines = cells.map(c => {
                        return c.innerText.trim().split(/\\n/).map(l => l.trim()).filter(l => l);
                    });
                    const maxLines = Math.max(...cellLines.map(l => l.length));

                    if (maxLines <= 1) {
                        text += cellLines.map(l => l[0] || '').join(' | ') + '\\n';
                    } else {
                        for (let i = 0; i < maxLines; i++) {
                            const row = cellLines.map(l => {
                                if (l.length === 1) return l[0];
                                return l[i] || '';
                            });
                            text += row.join(' | ') + '\\n';
                        }
                    }
                });
                table.replaceWith(document.createTextNode(text));
            });

            return clone.innerText;
        }""", selector)

        content = content.replace('\xa0', ' ')
        content = re.sub(r'^[ \t]+$', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()

    async def parse_detail(self, url: str) -> Dict[str, Any]:
        """
        상세 페이지에서 본문과 첨부파일 파싱 (detail_page 사용)

        Returns:
            {"content": "본문 내용", "attachments": [{"name": "파일명", "url": "링크"}]}
        """
        try:
            await self.detail_page.goto(url, wait_until="networkidle", timeout=30000)
            await self.detail_page.wait_for_timeout(1000)

            # 본문 추출 (표→파이프 구분, AI/MCP 가독성 최적화)
            content = await self._extract_content(self.content_selector)

            # 첨부파일 추출
            attachments = []
            file_els = await self.detail_page.query_selector_all(self.attachment_selector)
            for file_el in file_els:
                try:
                    href = await file_el.get_attribute("href")
                    name = await file_el.inner_text()
                    name = name.strip()

                    # 유효한 파일 링크만
                    if href and name and len(name) < 200:
                        # 상대 URL 변환
                        if href.startswith("/"):
                            href = f"{self.base_domain}{href}"
                        elif not href.startswith("http"):
                            continue

                        # 외부 링크 제외 (같은 도메인만)
                        if self.base_domain and self.base_domain not in href:
                            continue

                        attachments.append({"name": name, "url": href})
                except Exception:
                    continue

            return {"content": content, "attachments": attachments}

        except Exception as e:
            logger.error(f"[{self.board_name}] 상세 페이지 파싱 오류 ({url}): {e}")
            return {"content": "", "attachments": []}

    async def _navigate_to_page(self, url: str, page_num: int) -> bool:
        """
        페이지 이동 - 서브클래스에서 오버라이드하여 페이지네이션 방식 변경

        Returns:
            True: 이동 성공, False: 더 이상 페이지 없음
        """
        separator = "&" if "?" in url else "?"
        page_url = f"{url}{separator}{self.pagination_param}={page_num}"
        await self.page.goto(page_url, wait_until="networkidle", timeout=30000)
        await self.page.wait_for_timeout(2000)
        return True

    async def parse_list(self, url: str, max_pages: Optional[int] = None, min_year: int = 2025) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """목록 페이지 파싱 - 페이지 단위로 yield (메모리 절약)"""
        logger.info(f"[{self.board_name}] 크롤링 시작: {url} (min_year={min_year})")
        current_page = 1
        stop_crawling = False

        while not stop_crawling:
            if not await self._navigate_to_page(url, current_page):
                break

            rows = await self.page.query_selector_all(self.row_selector)
            logger.info(f"[{self.board_name}] 페이지 {current_page}: {len(rows)}행")

            if not rows:
                break

            page_notices = []
            for row in rows:
                try:
                    notice = await self.parse_row(row, url)
                    if not notice:
                        continue

                    # 연도 체크
                    if notice.get("date"):
                        try:
                            year = int(notice["date"][:4])
                            if year < min_year:
                                logger.info(f"[{self.board_name}] {min_year}년 이전 글 발견, 크롤링 중단")
                                stop_crawling = True
                                break
                        except (ValueError, IndexError):
                            pass

                    page_notices.append(notice)

                except Exception as e:
                    logger.error(f"[{self.board_name}] 행 파싱 오류: {e}")
                    continue

            if page_notices:
                yield page_notices

            if not page_notices or stop_crawling:
                break

            if max_pages and current_page >= max_pages:
                logger.info(f"[{self.board_name}] 최대 페이지({max_pages}) 도달")
                break

            current_page += 1

    async def crawl_and_save(self, urls: List[Dict[str, str]], max_pages: Optional[int] = None, min_year: int = 2025) -> Dict[str, int]:
        """크롤링 실행 및 MongoDB 저장 - 페이지 단위로 즉시 저장"""
        total_new = 0
        total_updated = 0

        for url_info in urls:
            try:
                no_new_pages = 0  # 연속으로 new=0인 페이지 수

                async for page_notices in self.parse_list(url_info["url"], max_pages=max_pages, min_year=min_year):
                    page_new = 0

                    for notice in page_notices:
                        # 이미 존재하는 공지인지 확인
                        existing = await Database.notices().find_one({"url": notice["url"]})

                        # 이미 content까지 있으면 스킵
                        if existing and existing.get("content"):
                            continue

                        # 새 공지이거나 content가 없으면 상세 페이지 크롤링
                        logger.info(f"[{self.board_name}] 상세 크롤링: {notice['title'][:30]}")
                        detail = await self.parse_detail(notice["url"])
                        notice["content"] = detail["content"]
                        notice["attachments"] = detail["attachments"]

                        # DB 저장
                        result = await Database.notices().update_one(
                            {"url": notice["url"]},
                            {
                                "$set": {
                                    "title": notice["title"],
                                    "author": notice.get("author"),
                                    "date": notice["date"],
                                    "content": notice.get("content", ""),
                                    "attachments": notice.get("attachments", []),
                                    "board_id": self.board_id,
                                    "board_name": self.board_name,
                                },
                                "$setOnInsert": {
                                    "crawled_at": datetime.utcnow()
                                }
                            },
                            upsert=True
                        )

                        if result.upserted_id:
                            total_new += 1
                            page_new += 1
                        elif result.modified_count:
                            total_updated += 1

                    logger.info(f"[{self.board_name}] 페이지 저장 완료: page_new={page_new}, total_new={total_new}, total_updated={total_updated}")

                    # 연속 2페이지 new=0이면 이전 데이터 도달로 판단, 중단
                    if page_new == 0:
                        no_new_pages += 1
                        if no_new_pages >= 2:
                            logger.info(f"[{self.board_name}] 새 공지 없음 (연속 {no_new_pages}페이지), 크롤링 중단")
                            break
                    else:
                        no_new_pages = 0

            except Exception as e:
                logger.error(f"[{self.board_name}] 크롤링 오류: {e}")
                continue

        await Database.boards().update_one(
            {"_id": self.board_id},
            {"$set": {"last_crawled_at": datetime.utcnow()}}
        )

        return {"new": total_new, "updated": total_updated}
