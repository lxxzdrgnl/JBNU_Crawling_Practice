"""
공지사항 서비스
REST API와 MCP가 공유하는 공지사항 조회 로직
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from app.core.database import Database


def _serialize_notice(n: Dict) -> Dict:
    """MongoDB 문서 → API 응답 직렬화"""
    return {
        "id": str(n["_id"]),
        "title": n["title"],
        "url": n["url"],
        "date": n["date"],
        "author": n.get("author"),
        "board_name": n["board_name"],
        "content": n.get("content", ""),
        "attachments": n.get("attachments", []),
        "board_id": str(n["board_id"]),
        "crawled_at": n["crawled_at"]
    }


async def _resolve_board_ids(board_slugs: List[str]) -> List:
    """slug 목록 → board ObjectId 목록"""
    boards = await Database.boards().find({"slug": {"$in": board_slugs}}).to_list(100)
    return [b["_id"] for b in boards]


async def get_notices(
    board_slugs: Optional[List[str]] = None,
    days: Optional[int] = None,
    page: int = 1,
    limit: int = 20
) -> Dict:
    """공지사항 목록 조회"""
    query = {}

    if board_slugs:
        board_ids = await _resolve_board_ids(board_slugs)
        if board_ids:
            query["board_id"] = {"$in": board_ids}

    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query["crawled_at"] = {"$gte": cutoff}

    total = await Database.notices().count_documents(query)

    skip = (page - 1) * limit
    cursor = Database.notices().find(query).sort("date", -1).skip(skip).limit(limit)
    notices = await cursor.to_list(limit)

    return {
        "notices": [_serialize_notice(n) for n in notices],
        "total": total,
        "page": page,
        "limit": limit
    }


async def search_notices(
    keyword: str,
    board_slugs: Optional[List[str]] = None,
    limit: int = 20
) -> List[Dict]:
    """공지사항 검색 (제목 + 본문)"""
    query = {"$text": {"$search": keyword}}

    if board_slugs:
        board_ids = await _resolve_board_ids(board_slugs)
        if board_ids:
            query["board_id"] = {"$in": board_ids}

    cursor = Database.notices().find(
        query,
        {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)

    notices = await cursor.to_list(limit)
    return [_serialize_notice(n) for n in notices]


async def get_notice_by_id(notice_id: str) -> Optional[Dict]:
    """단일 공지사항 조회"""
    try:
        oid = ObjectId(notice_id)
    except Exception:
        return None

    notice = await Database.notices().find_one({"_id": oid})
    if not notice:
        return None

    return _serialize_notice(notice)


async def get_boards() -> List[Dict]:
    """게시판 목록 조회"""
    boards = await Database.boards().find({"is_active": True}).to_list(100)

    return [
        {
            "id": str(b["_id"]),
            "slug": b.get("slug", ""),
            "name": b["name"],
            "group": b["group"],
            "color": b["color"],
            "is_active": b["is_active"],
            "last_crawled_at": b.get("last_crawled_at")
        }
        for b in boards
    ]


async def get_boards_by_group() -> Dict[str, List[Dict]]:
    """그룹별 게시판 목록 조회"""
    boards = await get_boards()

    result = {}
    for board in boards:
        group = board["group"]
        if group not in result:
            result[group] = []
        result[group].append(board)

    return result
