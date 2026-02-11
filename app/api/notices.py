"""
공지사항 REST API
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

from app.services import (
    get_notices,
    search_notices,
    get_notice_by_id,
    get_boards,
    get_boards_by_group,
    crawl_all,
    crawl_board
)
from app.models.db_models import NoticeListResponse, CrawlResponse, CrawlResult

router = APIRouter(prefix="/notices", tags=["notices"])


@router.get("")
async def list_notices(
    boards: Optional[str] = Query(None, description="게시판 slug (쉼표로 구분, 예: csai,swuniv)"),
    days: Optional[int] = Query(None, description="최근 N일"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 개수")
):
    """
    공지사항 목록 조회

    - **boards**: 게시판 slug 필터 (예: "csai,swuniv,student")
    - **days**: 최근 N일 이내 공지만
    - **page**: 페이지 번호
    - **limit**: 페이지당 개수

    사용 가능한 slug: student, seminar, study, eng, csai, swuniv
    """
    board_slugs = boards.split(",") if boards else None
    result = await get_notices(
        board_slugs=board_slugs,
        days=days,
        page=page,
        limit=limit
    )
    return result


@router.get("/search")
async def search(
    keyword: str = Query(..., description="검색 키워드"),
    boards: Optional[str] = Query(None, description="게시판 slug (쉼표로 구분)"),
    limit: int = Query(20, ge=1, le=100, description="최대 개수")
):
    """
    공지사항 검색 (제목 기준)

    - **keyword**: 검색할 키워드
    - **boards**: 게시판 slug 필터 (예: "csai,swuniv")
    - **limit**: 최대 결과 수
    """
    board_slugs = boards.split(",") if boards else None
    result = await search_notices(
        keyword=keyword,
        board_slugs=board_slugs,
        limit=limit
    )
    return {"notices": result, "count": len(result)}


@router.get("/boards")
async def list_boards():
    """
    게시판 목록 조회
    """
    boards = await get_boards()
    return {"boards": boards}


@router.get("/boards/grouped")
async def list_boards_by_group():
    """
    그룹별 게시판 목록 조회
    """
    groups = await get_boards_by_group()
    return {"groups": groups}


@router.get("/{notice_id}")
async def get_notice(notice_id: str):
    """
    단일 공지사항 조회
    """
    notice = await get_notice_by_id(notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice


@router.post("/crawl")
async def trigger_crawl(
    boards: Optional[str] = Query(None, description="게시판 slug (쉼표로 구분, 없으면 전체)")
):
    """
    크롤링 실행

    - **boards**: 특정 게시판만 크롤링 (예: "csai,swuniv", 없으면 전체)
    """
    board_slugs = boards.split(",") if boards else None
    result = await crawl_all(board_slugs=board_slugs)

    return {
        "success": True,
        "results": result["results"],
        "total_new": result["total_new"],
        "total_updated": result["total_updated"]
    }
