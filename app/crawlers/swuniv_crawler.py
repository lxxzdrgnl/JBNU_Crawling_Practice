"""
SW중심대학사업단 크롤러
URL 패턴: swuniv.jbnu.ac.kr/main/jbnusw?gc=605XOAS
"""
import logging
from typing import Dict, Any, Optional
from .base import BaseCrawler

logger = logging.getLogger(__name__)


class SwunivCrawler(BaseCrawler):
    """SW중심대학사업단 크롤러"""

    row_selector = "table tbody tr"
    base_domain = "https://swuniv.jbnu.ac.kr"
    content_selector = ".content_wrap"
    attachment_selector = "a[href*='download'], a[href*='file']"

    async def _navigate_to_page(self, url: str, page_num: int) -> bool:
        """SWUNIV 특수 URL 패턴 페이지네이션"""
        page_url = f"{url}&do=list&page={page_num}"
        await self.page.goto(page_url, wait_until="networkidle", timeout=30000)
        await self.page.wait_for_timeout(2000)
        return True

    async def parse_row(self, row, base_url: str) -> Optional[Dict[str, Any]]:
        """단일 행 파싱"""
        title_el = await row.query_selector("td a")
        if not title_el:
            return None

        title = await title_el.inner_text()
        href = await title_el.get_attribute("href")

        if not href:
            return None

        # URL 처리
        if not href.startswith("http"):
            if href.startswith("/"):
                full_url = f"{self.base_domain}{href}"
            elif "?" in href:
                full_url = f"{self.base_domain}/main/jbnusw{href}"
            else:
                full_url = f"{self.base_domain}/main/{href}"
        else:
            full_url = href

        # 날짜와 작성자 찾기
        cells = await row.query_selector_all("td")
        date_text = ""
        author = None

        for i, cell in enumerate(cells):
            text = await cell.inner_text()
            text = text.strip()

            # 날짜 패턴 체크 (YYYY-MM-DD)
            if len(text) == 10 and text[4] == "-" and text[7] == "-":
                date_text = text
            elif i == 3 and not text.isdigit() and len(text) < 20:
                author = text

        return {
            "url": full_url,
            "title": title.strip(),
            "date": date_text,
            "author": author
        }
