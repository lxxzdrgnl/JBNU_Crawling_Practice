"""
DB 초기화 스크립트
MongoDB 연결, 인덱스 생성, 초기 데이터 입력

사용법:
    python scripts/init_db.py
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import Database, init_boards


async def main():
    """DB 초기화"""
    print("=" * 50)
    print("🗄️  MongoDB 초기화 시작")
    print("=" * 50)

    # MongoDB 연결
    await Database.connect()

    # 인덱스 생성
    await Database.create_indexes()

    # 초기 게시판 데이터 입력
    await init_boards()

    # 연결 종료
    await Database.disconnect()

    print("=" * 50)
    print("✅ MongoDB 초기화 완료")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
