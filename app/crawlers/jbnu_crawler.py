"""
전북대학교 메인 크롤러
URL 패턴: www.jbnu.ac.kr/web/news/notice/subXX.do
페이지네이션: 클릭 + navigation 방식 (POST form submit)
"""
import re
import logging
from typing import Dict, Any, Optional
from .base import BaseCrawler

logger = logging.getLogger(__name__)


class JbnuCrawler(BaseCrawler):
    """전북대학교 메인 크롤러"""

    row_selector = "table tbody tr"
    base_domain = "https://www.jbnu.ac.kr"
    content_selector = ".com-post-content-01"
    attachment_selector = ".file-wrap a, .attachFile a, a[href*='fileDown']"

    async def _navigate_to_page(self, url: str, page_num: int) -> bool:
        """JBNU는 클릭 방식 페이지네이션"""
        if page_num == 1:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await self.page.wait_for_timeout(2000)
            return True

        next_btn = await self.page.query_selector(f'[onclick="pf_LinkPage({page_num})"]')
        if not next_btn:
            logger.info(f"[{self.board_name}] 마지막 페이지 도달")
            return False

        try:
            async with self.page.expect_navigation(wait_until="networkidle"):
                await next_btn.click()
            await self.page.wait_for_timeout(1000)
            return True
        except Exception as e:
            logger.error(f"[{self.board_name}] 페이지 이동 오류: {e}")
            return False

    async def parse_row(self, row, base_url: str) -> Optional[Dict[str, Any]]:
        """단일 행 파싱"""
        title_el = await row.query_selector("td.td-title a, td a.title")
        if not title_el:
            return None

        onclick = await title_el.get_attribute("onclick")
        if not onclick or "pf_DetailMove" not in onclick:
            return None

        match = re.search(r"pf_DetailMove\(['\"]?(\d+)['\"]?\)", onclick)
        if not match:
            return None

        post_id = match.group(1)
        full_url = f"{self.base_domain}/web/Board/{post_id}/detailView.do"

        title = await title_el.inner_text()
        title = title.strip()

        # 날짜 추출
        date_text = ""
        etc_list = await row.query_selector("ul.etc-list li")
        if etc_list:
            date_text = await etc_list.inner_text()
            date_text = date_text.strip()

        # 작성자 추출
        cells = await row.query_selector_all("td")
        author = None
        if len(cells) >= 5:
            author = await cells[4].inner_text()
            author = author.strip() if author else None

        return {
            "url": full_url,
            "title": title,
            "date": date_text,
            "author": author
        }
