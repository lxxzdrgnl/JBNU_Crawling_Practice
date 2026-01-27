"""
JBNU LMS Crawler - FastAPI 서버 실행

사용법:
    python main.py
    또는
    uvicorn app.main:app --reload
"""

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🚀 JBNU LMS Crawler API 서버 시작")
    print("=" * 60)
    print("📍 API 문서: http://localhost:8000/docs")
    print("📍 서버 주소: http://localhost:8000")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
