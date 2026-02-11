"""
JBNU 공지사항 크롤러 MCP 서버

Claude가 전북대 공지사항을 조회할 수 있도록 하는 MCP 서버

사용법:
    uv run python mcp_server.py
"""
from typing import Optional, List
from fastmcp import FastMCP

from app.core.database import Database, init_boards
from app.services import (
    get_notices,
    search_notices,
    get_boards,
    get_boards_by_group,
    crawl_all
)
from app.config import settings

# MCP 서버 생성
mcp = FastMCP("JBNU 공지사항 크롤러")


# ============================================================
# 공지사항 관련 도구
# ============================================================

@mcp.tool()
async def get_latest_notices(
    boards: Optional[List[str]] = None,
    days: int = 7,
    limit: int = 20
) -> dict:
    """
    최신 공지사항을 가져옵니다.

    Args:
        boards: 게시판 slug 목록 (예: ["csai", "swuniv", "student"])
        days: 최근 N일 (기본: 7일)
        limit: 최대 개수 (기본: 20개)

    Returns:
        최신 공지사항 목록

    예시:
        - "오늘 새 공지 있어?" → get_latest_notices(days=1)
        - "이번 주 컴공 공지" → get_latest_notices(boards=["csai"], days=7)
    """
    await _ensure_db_connected()

    result = await get_notices(
        board_slugs=boards,
        days=days,
        page=1,
        limit=limit
    )

    return {
        "status": "success",
        "count": len(result["notices"]),
        "total": result["total"],
        "notices": result["notices"]
    }


@mcp.tool()
async def search_jbnu_notices(
    keyword: str,
    boards: Optional[List[str]] = None,
    limit: int = 20
) -> dict:
    """
    공지사항을 키워드로 검색합니다. (제목 기준)

    Args:
        keyword: 검색 키워드 (예: "장학금", "취업", "특강")
        boards: 게시판 slug 목록 (없으면 전체 검색)
        limit: 최대 개수 (기본: 20개)

    Returns:
        검색된 공지사항 목록

    예시:
        - "장학금 관련 공지 찾아줘" → search_jbnu_notices("장학금")
        - "컴공 취업 공지" → search_jbnu_notices("취업", boards=["csai"])
    """
    await _ensure_db_connected()

    notices = await search_notices(
        keyword=keyword,
        board_slugs=boards,
        limit=limit
    )

    return {
        "status": "success",
        "keyword": keyword,
        "count": len(notices),
        "notices": notices
    }


@mcp.tool()
async def list_notice_boards() -> dict:
    """
    사용 가능한 게시판 목록을 반환합니다.
    그룹별(전북대, 단과대, 학과, 사업단)로 정리되어 있습니다.

    Returns:
        게시판 목록 (그룹별)
    """
    await _ensure_db_connected()

    groups = await get_boards_by_group()

    return {
        "status": "success",
        "groups": groups
    }


@mcp.tool()
async def trigger_notice_crawl(boards: Optional[List[str]] = None) -> dict:
    """
    공지사항 크롤링을 실행합니다.

    Args:
        boards: 크롤링할 게시판 slug 목록 (없으면 전체)

    Returns:
        크롤링 결과 (새로 추가된 공지 수, 업데이트된 수)

    예시:
        - "공지 새로고침해줘" → trigger_notice_crawl()
        - "컴공 공지만 업데이트" → trigger_notice_crawl(boards=["csai"])
    """
    await _ensure_db_connected()

    result = await crawl_all(board_slugs=boards)

    return {
        "status": "success",
        "total_new": result["total_new"],
        "total_updated": result["total_updated"],
        "details": result["results"]
    }


# ============================================================
# 유틸리티
# ============================================================

_db_connected = False


async def _ensure_db_connected():
    """MongoDB 연결 확인 및 연결"""
    global _db_connected
    if not _db_connected:
        await Database.connect(
            uri=settings.MONGODB_URI,
            db_name=settings.MONGODB_DB_NAME
        )
        await init_boards()
        _db_connected = True


if __name__ == "__main__":
    mcp.run()
