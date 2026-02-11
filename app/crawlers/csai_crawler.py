"""
컴퓨터인공지능학부 크롤러
URL 패턴: csai.jbnu.ac.kr/csai/{board_id}/subview.do
"""
from typing import Dict, Any, Optional
from .base import BaseCrawler


class CSAICrawler(BaseCrawler):
    """컴퓨터인공지능학부 크롤러"""

    row_selector = ".artclTable tbody tr"
    base_domain = "https://csai.jbnu.ac.kr"
    content_selector = ".artclView"
    attachment_selector = ".artclItem a[href*='download'], .artclItem a[href*='file'], .file-wrap a"

    async def parse_row(self, row, base_url: str) -> Optional[Dict[str, Any]]:
        """단일 행 파싱"""
        # 상단 고정 공지 건너뛰기 (class="headline" 또는 번호가 숫자가 아닌 경우)
        row_class = await row.get_attribute("class") or ""
        if "headline" in row_class:
            return None

        num_el = await row.query_selector("td:nth-child(1)")
        if num_el:
            num_text = await num_el.inner_text()
            if not num_text.strip().isdigit():
                return None

        title_el = await row.query_selector("td.artclTitle a, td a")
        if not title_el:
            return None

        title = await title_el.inner_text()
        href = await title_el.get_attribute("href")

        if not href:
            return None

        # 상대 URL을 절대 URL로 변환
        if not href.startswith("http"):
            full_url = f"{self.base_domain}{href}"
        else:
            full_url = href

        # 날짜 (4번째 열)
        date_el = await row.query_selector("td:nth-child(4)")
        date_text = ""
        if date_el:
            date_text = await date_el.inner_text()
            date_text = date_text.strip().replace(".", "-")

        # 작성자 (3번째 열)
        author_el = await row.query_selector("td:nth-child(3)")
        author = None
        if author_el:
            author = await author_el.inner_text()
            author = author.strip() if author else None

        return {
            "url": full_url,
            "title": title.strip(),
            "date": date_text,
            "author": author
        }
