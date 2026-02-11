"""
공과대학 크롤러
URL 패턴: eng.jbnu.ac.kr/{path}/notice
Vue SPA 기반 - 상세 URL에 ?type=board 필수, 첨부파일은 버튼 클릭 다운로드
"""
import logging
from typing import Dict, Any, Optional
from .base import BaseCrawler

logger = logging.getLogger(__name__)


class EngCrawler(BaseCrawler):
    """공과대학 크롤러"""

    row_selector = "table tbody tr"
    base_domain = "https://eng.jbnu.ac.kr"
    content_selector = ".content_wrap"

    async def parse_detail(self, url: str) -> Dict[str, Any]:
        """ENG 상세 페이지 파싱 - 첨부파일은 button 클릭으로 다운로드 URL 추출"""
        try:
            await self.detail_page.goto(url, wait_until="networkidle", timeout=30000)
            await self.detail_page.wait_for_timeout(2000)

            # 본문 추출 (표→파이프 구분, AI/MCP 가독성 최적화)
            content = await self._extract_content(self.content_selector)

            # 첨부파일 추출 - 버튼 클릭 → download 이벤트에서 URL 캡처
            attachments = []
            file_items = await self.detail_page.query_selector_all(".file_item")
            for item in file_items:
                try:
                    name_el = await item.query_selector("span")
                    btn = await item.query_selector("button")
                    if not name_el or not btn:
                        continue

                    name = await name_el.inner_text()
                    name = name.strip()
                    if not name:
                        continue

                    async with self.detail_page.expect_download(timeout=5000) as download_info:
                        await btn.click()
                    download = await download_info.value
                    download_url = download.url
                    await download.cancel()

                    attachments.append({"name": name, "url": download_url})
                except Exception:
                    continue

            return {"content": content, "attachments": attachments}

        except Exception as e:
            logger.error(f"[공과대학] 상세 페이지 파싱 오류 ({url}): {e}")
            return {"content": "", "attachments": []}

    async def parse_row(self, row, base_url: str) -> Optional[Dict[str, Any]]:
        """단일 행 파싱"""
        cells = await row.query_selector_all("td")
        if len(cells) < 4:
            return None

        # td[0]: 글 번호
        post_id = await cells[0].inner_text()
        post_id = post_id.strip()
        if not post_id.isdigit():
            return None

        # td[1]: 제목
        title_el = await cells[1].query_selector("a")
        if not title_el:
            return None
        title = await title_el.inner_text()
        title = title.strip()

        # URL 생성 (Vue SPA - type=board 파라미터 필수)
        full_url = f"{base_url}/detail/{post_id}?type=board"

        # td[2]: 작성자
        author = await cells[2].inner_text()
        author = author.strip() if author else None

        # td[3]: 날짜
        date_text = await cells[3].inner_text()
        date_text = date_text.strip()[:10]

        return {
            "url": full_url,
            "title": title,
            "date": date_text,
            "author": author
        }
