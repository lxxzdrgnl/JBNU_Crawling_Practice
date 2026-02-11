"""
JBNU 공지사항 크롤러 - 서버 실행

사용법:
    python main.py              # FastAPI 서버 실행
    python main.py --mcp        # MCP 서버 실행 (Claude 연동)

    또는

    uvicorn app.main:app --reload     # FastAPI
    uv run python mcp_server.py       # MCP
"""
import sys


def main():
    # MCP 모드 체크
    if "--mcp" in sys.argv:
        print("=" * 50)
        print("🤖 MCP 서버 모드로 실행")
        print("=" * 50)
        from mcp_server import mcp
        mcp.run()
    else:
        # FastAPI 서버 실행
        import uvicorn
        from app.config import settings

        print("=" * 60)
        print("🚀 JBNU 공지사항 크롤러 API 서버")
        print("=" * 60)
        print(f"📍 API 문서: http://localhost:{settings.API_PORT}/docs")
        print(f"📍 서버 주소: http://localhost:{settings.API_PORT}")
        print("=" * 60)
        print()
        print("💡 MCP 서버로 실행하려면: python main.py --mcp")
        print()

        uvicorn.run(
            "app.main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.DEBUG
        )


if __name__ == "__main__":
    main()
