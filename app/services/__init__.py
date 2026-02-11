"""
서비스 레이어
REST API와 MCP가 공유하는 비즈니스 로직
"""
from .crawl_service import crawl_board, crawl_all
from .notice_service import (
    get_notices,
    search_notices,
    get_notice_by_id,
    get_boards,
    get_boards_by_group
)

__all__ = [
    "crawl_board",
    "crawl_all",
    "get_notices",
    "search_notices",
    "get_notice_by_id",
    "get_boards",
    "get_boards_by_group"
]
