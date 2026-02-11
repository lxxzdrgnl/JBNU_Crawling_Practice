"""
JBNU 공지사항 크롤러 - FastAPI 앱

REST API와 MCP 서버에서 사용되는 메인 애플리케이션
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import notices
from app.core.database import Database, init_boards
from app.config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 이벤트"""
    # ===== 시작 =====
    print("=" * 50)
    print("🚀 JBNU 공지사항 크롤러 API 시작")
    print("=" * 50)

    # MongoDB 연결
    await Database.connect(
        uri=settings.MONGODB_URI,
        db_name=settings.MONGODB_DB_NAME
    )

    # 인덱스 생성 (없으면)
    await Database.create_indexes()

    # 초기 게시판 데이터 (없으면)
    await init_boards()

    print(f"📍 API 문서: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("=" * 50)

    yield

    # ===== 종료 =====
    print("🛑 서버 종료 중...")
    await Database.disconnect()


# FastAPI 앱 생성
app = FastAPI(
    title="JBNU 공지사항 크롤러 API",
    description="""
전북대학교 공지사항을 크롤링하고 조회하는 API

## 기능
- 📢 공지사항 조회 및 검색
- 🔄 크롤링 실행
- 📋 게시판 관리
    """,
    version="2.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(notices.router)


@app.get("/health")
async def health_check():
    """헬스체크"""
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
