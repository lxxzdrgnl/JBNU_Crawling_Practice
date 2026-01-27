from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
from app.api import auth, crawler
from app.core.browser import browser_manager

# HTTPBearer 보안 스키마 정의
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    앱 시작/종료 시 실행되는 이벤트
    """
    # 시작 시
    print("🚀 FastAPI 서버 시작")
    await browser_manager.initialize()

    yield

    # 종료 시
    print("🛑 FastAPI 서버 종료")
    await browser_manager.close()


# FastAPI 앱 생성
app = FastAPI(
    title="JBNU LMS Crawler API",
    description="전북대 스마트학습관리시스템 크롤링 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (프론트엔드에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(crawler.router)


@app.get("/health")
async def health_check():
    """
    헬스체크 엔드포인트
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # 개발 중에는 True, 프로덕션에서는 False
    )
