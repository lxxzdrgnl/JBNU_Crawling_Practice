"""
MongoDB 모델 정의 (Pydantic)
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any
from bson import ObjectId


class PyObjectId(ObjectId):
    """MongoDB ObjectId를 Pydantic에서 사용하기 위한 클래스"""

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


# ========== 게시판 관련 ==========

class BoardUrl(BaseModel):
    """게시판 URL 정보"""
    url: str
    name: str  # "학사공지", "장학공지" 등


class BoardInDB(BaseModel):
    """MongoDB boards 컬렉션 모델"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str                         # "컴퓨터인공지능학부"
    group: str                        # "전북대", "단과대", "학과", "사업단"
    urls: List[BoardUrl]
    crawler_type: str                 # "csai", "eng", "jbnu", "swuniv"
    color: str                        # "#4CAF50"
    is_active: bool = True
    last_crawled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "arbitrary_types_allowed": True
    }


class BoardResponse(BaseModel):
    """게시판 API 응답 모델"""
    id: str
    name: str
    group: str
    color: str
    is_active: bool
    last_crawled_at: Optional[datetime] = None


# ========== 공지사항 관련 ==========

class NoticeInDB(BaseModel):
    """MongoDB notices 컬렉션 모델"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    url: str                          # unique
    title: str
    author: Optional[str] = None
    date: str                         # "2026-01-30"
    board_id: PyObjectId
    board_name: str                   # denormalized
    crawled_at: datetime

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "arbitrary_types_allowed": True
    }


class NoticeResponse(BaseModel):
    """공지사항 API 응답 모델"""
    id: str
    url: str
    title: str
    author: Optional[str] = None
    date: str
    board_id: str
    board_name: str
    crawled_at: datetime


class NoticeListResponse(BaseModel):
    """공지사항 목록 API 응답"""
    notices: List[NoticeResponse]
    total: int
    page: int
    limit: int


# ========== 크롤링 관련 ==========

class CrawlResult(BaseModel):
    """크롤링 결과"""
    board_name: str
    new_count: int
    updated_count: int
    error: Optional[str] = None


class CrawlResponse(BaseModel):
    """크롤링 API 응답"""
    success: bool
    results: List[CrawlResult]
    total_new: int
    total_updated: int
