"""
크롤링 서비스
REST API와 MCP가 공유하는 크롤링 로직
"""
from typing import Dict, List, Optional
from bson import ObjectId

from app.core.database import Database
from app.crawlers import CRAWLER_MAP


async def crawl_board(board_id: str) -> Dict:
    """
    특정 게시판 크롤링

    Args:
        board_id: 게시판 ObjectId (문자열)

    Returns:
        {"board_name": "...", "new": 0, "updated": 0, "error": None}
    """
    # ObjectId 변환
    try:
        oid = ObjectId(board_id)
    except Exception:
        return {"board_name": "unknown", "new": 0, "updated": 0, "error": "Invalid board_id"}

    # 게시판 조회
    board = await Database.boards().find_one({"_id": oid})
    if not board:
        return {"board_name": "unknown", "new": 0, "updated": 0, "error": "Board not found"}

    # 크롤러 선택
    crawler_class = CRAWLER_MAP.get(board["crawler_type"])
    if not crawler_class:
        return {
            "board_name": board["name"],
            "new": 0,
            "updated": 0,
            "error": f"Unknown crawler type: {board['crawler_type']}"
        }

    # 크롤링 실행
    try:
        async with crawler_class(board["_id"], board["name"]) as crawler:
            result = await crawler.crawl_and_save(board["urls"])

        return {
            "board_name": board["name"],
            "new": result["new"],
            "updated": result["updated"],
            "error": None
        }

    except Exception as e:
        return {
            "board_name": board["name"],
            "new": 0,
            "updated": 0,
            "error": str(e)
        }


async def crawl_all(board_slugs: Optional[List[str]] = None) -> Dict:
    """
    모든 (또는 특정) 게시판 크롤링

    Args:
        board_slugs: 크롤링할 게시판 slug 목록 (None이면 전체)

    Returns:
        {"results": [...], "total_new": 0, "total_updated": 0}
    """
    # 게시판 조회
    query = {"is_active": True}
    if board_slugs:
        query["slug"] = {"$in": board_slugs}

    boards = await Database.boards().find(query).to_list(100)

    results = []
    total_new = 0
    total_updated = 0

    for board in boards:
        result = await crawl_board(str(board["_id"]))
        results.append(result)

        if not result.get("error"):
            total_new += result["new"]
            total_updated += result["updated"]

    return {
        "results": results,
        "total_new": total_new,
        "total_updated": total_updated
    }


async def get_crawl_status() -> Dict:
    """
    크롤링 상태 조회

    Returns:
        {"boards": [{"name": "...", "last_crawled_at": "..."}]}
    """
    boards = await Database.boards().find({"is_active": True}).to_list(100)

    return {
        "boards": [
            {
                "name": board["name"],
                "last_crawled_at": board.get("last_crawled_at")
            }
            for board in boards
        ]
    }
