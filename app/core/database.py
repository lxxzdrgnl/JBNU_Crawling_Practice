"""
MongoDB 연결 관리 모듈
Motor (비동기 MongoDB 드라이버) 사용
"""
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional


class Database:
    """MongoDB 연결 관리 클래스"""

    client: Optional[AsyncIOMotorClient] = None
    db = None

    @classmethod
    async def connect(cls, uri: str = "mongodb://localhost:27017", db_name: str = "jbnu_notices"):
        """MongoDB 연결"""
        cls.client = AsyncIOMotorClient(uri)
        cls.db = cls.client[db_name]

        # 연결 테스트
        await cls.client.admin.command('ping')
        print(f"MongoDB 연결 성공: {db_name}")

    @classmethod
    async def disconnect(cls):
        """MongoDB 연결 종료"""
        if cls.client:
            cls.client.close()
            print("MongoDB 연결 종료")

    @classmethod
    def notices(cls):
        """notices 컬렉션 반환"""
        return cls.db.notices

    @classmethod
    def boards(cls):
        """boards 컬렉션 반환"""
        return cls.db.boards

    @classmethod
    async def create_indexes(cls):
        """인덱스 생성"""
        # notices 인덱스
        await cls.notices().create_index("url", unique=True)
        await cls.notices().create_index([("board_id", 1), ("date", -1)])
        await cls.notices().create_index([("date", -1)])

        # 텍스트 검색 인덱스 (제목 + 본문)
        await cls.notices().create_index(
            [("title", "text"), ("content", "text")],
            default_language="none",
            name="title_content_text"
        )

        # boards 인덱스
        await cls.boards().create_index("group")
        await cls.boards().create_index("is_active")

        print("인덱스 생성 완료")


# 초기 게시판 데이터
INITIAL_BOARDS = [
    # ========== 전북대 그룹 ==========
    {
        "name": "학생공지",
        "slug": "student",
        "group": "전북대",
        "urls": [{"url": "https://www.jbnu.ac.kr/web/news/notice/sub01.do", "name": "학생공지"}],
        "crawler_type": "jbnu",
        "color": "#2196F3",
        "is_active": True
    },
    {
        "name": "특강&세미나",
        "slug": "seminar",
        "group": "전북대",
        "urls": [{"url": "https://www.jbnu.ac.kr/web/news/notice/sub02.do", "name": "특강&세미나"}],
        "crawler_type": "jbnu",
        "color": "#2196F3",
        "is_active": True
    },
    {
        "name": "공모/스터디",
        "slug": "study",
        "group": "전북대",
        "urls": [{"url": "https://www.jbnu.ac.kr/web/news/notice/sub05.do", "name": "공모/스터디"}],
        "crawler_type": "jbnu",
        "color": "#2196F3",
        "is_active": True
    },

    # ========== 단과대 그룹 ==========
    {
        "name": "공과대학",
        "slug": "eng",
        "group": "단과대",
        "urls": [
            {"url": "https://eng.jbnu.ac.kr/eng/38/notice", "name": "공지사항"},
            {"url": "https://eng.jbnu.ac.kr/freshman/34/notice", "name": "신입생"}
        ],
        "crawler_type": "eng",
        "color": "#9E9E9E",
        "is_active": True
    },

    # ========== 학과 그룹 ==========
    {
        "name": "컴퓨터인공지능학부",
        "slug": "csai",
        "group": "학과",
        "urls": [
            {"url": "https://csai.jbnu.ac.kr/csai/29105/subview.do", "name": "학사공지"},
            {"url": "https://csai.jbnu.ac.kr/csai/29106/subview.do", "name": "장학공지"},
            {"url": "https://csai.jbnu.ac.kr/csai/29107/subview.do", "name": "취업공지"},
            {"url": "https://csai.jbnu.ac.kr/csai/29108/subview.do", "name": "행사공지"},
            {"url": "https://csai.jbnu.ac.kr/csai/29109/subview.do", "name": "기타공지"}
        ],
        "crawler_type": "csai",
        "color": "#4CAF50",
        "is_active": True
    },

    # ========== 사업단 그룹 ==========
    {
        "name": "SW중심대학사업단",
        "slug": "swuniv",
        "group": "사업단",
        "urls": [{"url": "https://swuniv.jbnu.ac.kr/main/jbnusw?gc=605XOAS", "name": "공지사항"}],
        "crawler_type": "swuniv",
        "color": "#FF9800",
        "is_active": True
    }
]


async def init_boards():
    """초기 게시판 데이터 입력 (없으면 생성, slug 업데이트)"""
    for board_data in INITIAL_BOARDS:
        # slug가 없는 기존 데이터도 업데이트
        await Database.boards().update_one(
            {"name": board_data["name"]},
            {
                "$set": {"slug": board_data["slug"]},
                "$setOnInsert": {k: v for k, v in board_data.items() if k != "slug"}
            },
            upsert=True
        )
    print(f"초기 게시판 데이터 입력 완료: {len(INITIAL_BOARDS)}개")
